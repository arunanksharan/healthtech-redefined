"""
Medical NLP Service

Natural Language Processing for medical text:
- Named Entity Recognition (NER)
- Medical concept extraction
- ICD/SNOMED coding suggestions
- Sentiment analysis
- Negation detection

EPIC-009: US-009.2 Medical NLP
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4
import re
import logging

logger = logging.getLogger(__name__)


class EntityType(str, Enum):
    """Types of clinical entities."""
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
    FAMILY_HISTORY = "family_history"
    ALLERGY = "allergy"


class NegationStatus(str, Enum):
    """Negation status for entities."""
    AFFIRMED = "affirmed"
    NEGATED = "negated"
    UNCERTAIN = "uncertain"
    HYPOTHETICAL = "hypothetical"
    FAMILY_HISTORY = "family_history"


@dataclass
class ClinicalEntity:
    """An extracted clinical entity."""
    entity_id: str
    entity_type: EntityType
    text: str
    normalized_text: str

    # Position in text
    start_offset: int
    end_offset: int

    # Coding
    codes: List[Dict[str, str]] = field(default_factory=list)  # [{"system": "SNOMED", "code": "...", "display": "..."}]

    # Context
    negation_status: NegationStatus = NegationStatus.AFFIRMED
    confidence: float = 0.9

    # Related entities
    modifiers: List[str] = field(default_factory=list)
    related_entities: List[str] = field(default_factory=list)


@dataclass
class EntityExtraction:
    """Result of entity extraction from text."""
    extraction_id: str
    input_text: str

    entities: List[ClinicalEntity] = field(default_factory=list)

    # Metadata
    processing_time_ms: float = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class SentimentResult:
    """Sentiment analysis result."""
    text: str
    sentiment: str  # positive, negative, neutral
    score: float  # -1 to 1
    emotions: Dict[str, float] = field(default_factory=dict)


@dataclass
class CodingSuggestion:
    """Suggested medical code for text."""
    code: str
    system: str  # ICD-10, SNOMED, CPT
    display: str
    confidence: float
    evidence_text: str


class MedicalNLPService:
    """
    Medical NLP service for clinical text processing.

    Provides:
    - Named Entity Recognition
    - Medical concept normalization
    - Code suggestions
    - Negation detection
    - Section parsing
    """

    def __init__(self):
        # Medical terminology patterns
        self._symptom_patterns = self._load_symptom_patterns()
        self._medication_patterns = self._load_medication_patterns()
        self._anatomy_patterns = self._load_anatomy_patterns()
        self._condition_patterns = self._load_condition_patterns()

        # Negation patterns
        self._negation_patterns = [
            r"\bno\b", r"\bnot\b", r"\bnever\b", r"\bwithout\b",
            r"\bdenies\b", r"\bdenied\b", r"\bnegative\b",
            r"\brules out\b", r"\brule out\b",
        ]

        # SNOMED code mappings (subset)
        self._snomed_mappings = self._load_snomed_mappings()

        # ICD-10 mappings (subset)
        self._icd10_mappings = self._load_icd10_mappings()

    def _load_symptom_patterns(self) -> Dict[str, str]:
        """Load symptom pattern mappings."""
        return {
            r"\b(headache|cephalalgia)\b": "headache",
            r"\b(chest pain|chest discomfort)\b": "chest_pain",
            r"\b(shortness of breath|dyspnea|sob)\b": "dyspnea",
            r"\b(nausea|nauseated)\b": "nausea",
            r"\b(vomiting|emesis)\b": "vomiting",
            r"\b(diarrhea|loose stools)\b": "diarrhea",
            r"\b(fever|febrile|pyrexia)\b": "fever",
            r"\b(cough|coughing)\b": "cough",
            r"\b(fatigue|tired|exhaustion)\b": "fatigue",
            r"\b(dizziness|dizzy|vertigo|lightheaded)\b": "dizziness",
            r"\b(pain|painful|ache|aching)\b": "pain",
            r"\b(swelling|swollen|edema)\b": "swelling",
            r"\b(rash|skin eruption)\b": "rash",
            r"\b(anxiety|anxious)\b": "anxiety",
            r"\b(depression|depressed)\b": "depression",
        }

    def _load_medication_patterns(self) -> Dict[str, str]:
        """Load medication pattern mappings."""
        return {
            r"\b(aspirin|asa)\b": "aspirin",
            r"\b(ibuprofen|advil|motrin)\b": "ibuprofen",
            r"\b(acetaminophen|tylenol|apap)\b": "acetaminophen",
            r"\b(lisinopril)\b": "lisinopril",
            r"\b(metformin)\b": "metformin",
            r"\b(atorvastatin|lipitor)\b": "atorvastatin",
            r"\b(omeprazole|prilosec)\b": "omeprazole",
            r"\b(amlodipine|norvasc)\b": "amlodipine",
            r"\b(metoprolol|lopressor)\b": "metoprolol",
            r"\b(levothyroxine|synthroid)\b": "levothyroxine",
        }

    def _load_anatomy_patterns(self) -> Dict[str, str]:
        """Load anatomy pattern mappings."""
        return {
            r"\b(head)\b": "head",
            r"\b(neck)\b": "neck",
            r"\b(chest|thorax)\b": "chest",
            r"\b(abdomen|stomach|belly)\b": "abdomen",
            r"\b(back)\b": "back",
            r"\b(arm|arms)\b": "arm",
            r"\b(leg|legs)\b": "leg",
            r"\b(hand|hands)\b": "hand",
            r"\b(foot|feet)\b": "foot",
            r"\b(heart|cardiac)\b": "heart",
            r"\b(lung|lungs|pulmonary)\b": "lung",
            r"\b(liver|hepatic)\b": "liver",
            r"\b(kidney|kidneys|renal)\b": "kidney",
        }

    def _load_condition_patterns(self) -> Dict[str, str]:
        """Load condition pattern mappings."""
        return {
            r"\b(diabetes|dm|diabetic)\b": "diabetes",
            r"\b(hypertension|htn|high blood pressure)\b": "hypertension",
            r"\b(asthma)\b": "asthma",
            r"\b(copd|chronic obstructive)\b": "copd",
            r"\b(heart failure|chf)\b": "heart_failure",
            r"\b(coronary artery disease|cad)\b": "cad",
            r"\b(depression|mdd)\b": "depression",
            r"\b(anxiety|gad)\b": "anxiety",
            r"\b(hypothyroid|hypothyroidism)\b": "hypothyroidism",
            r"\b(hyperlipidemia|high cholesterol)\b": "hyperlipidemia",
        }

    def _load_snomed_mappings(self) -> Dict[str, Dict[str, str]]:
        """Load SNOMED CT code mappings."""
        return {
            "headache": {"code": "25064002", "display": "Headache"},
            "chest_pain": {"code": "29857009", "display": "Chest pain"},
            "dyspnea": {"code": "267036007", "display": "Dyspnea"},
            "fever": {"code": "386661006", "display": "Fever"},
            "cough": {"code": "49727002", "display": "Cough"},
            "diabetes": {"code": "73211009", "display": "Diabetes mellitus"},
            "hypertension": {"code": "38341003", "display": "Hypertensive disorder"},
            "asthma": {"code": "195967001", "display": "Asthma"},
        }

    def _load_icd10_mappings(self) -> Dict[str, Dict[str, str]]:
        """Load ICD-10 code mappings."""
        return {
            "headache": {"code": "R51.9", "display": "Headache, unspecified"},
            "chest_pain": {"code": "R07.9", "display": "Chest pain, unspecified"},
            "dyspnea": {"code": "R06.00", "display": "Dyspnea, unspecified"},
            "fever": {"code": "R50.9", "display": "Fever, unspecified"},
            "diabetes": {"code": "E11.9", "display": "Type 2 diabetes mellitus"},
            "hypertension": {"code": "I10", "display": "Essential hypertension"},
            "asthma": {"code": "J45.909", "display": "Unspecified asthma"},
        }

    async def extract_entities(
        self,
        text: str,
        entity_types: Optional[List[EntityType]] = None,
    ) -> EntityExtraction:
        """
        Extract clinical entities from text.

        Args:
            text: Clinical text to process
            entity_types: Types of entities to extract (all if None)

        Returns:
            EntityExtraction with found entities
        """
        start_time = datetime.now(timezone.utc)

        extraction = EntityExtraction(
            extraction_id=str(uuid4()),
            input_text=text,
        )

        text_lower = text.lower()

        # Extract symptoms
        if not entity_types or EntityType.SYMPTOM in entity_types:
            for pattern, normalized in self._symptom_patterns.items():
                for match in re.finditer(pattern, text_lower):
                    entity = self._create_entity(
                        text, match, normalized, EntityType.SYMPTOM
                    )
                    extraction.entities.append(entity)

        # Extract medications
        if not entity_types or EntityType.MEDICATION in entity_types:
            for pattern, normalized in self._medication_patterns.items():
                for match in re.finditer(pattern, text_lower):
                    entity = self._create_entity(
                        text, match, normalized, EntityType.MEDICATION
                    )
                    extraction.entities.append(entity)

        # Extract conditions
        if not entity_types or EntityType.CONDITION in entity_types:
            for pattern, normalized in self._condition_patterns.items():
                for match in re.finditer(pattern, text_lower):
                    entity = self._create_entity(
                        text, match, normalized, EntityType.CONDITION
                    )
                    extraction.entities.append(entity)

        # Extract anatomy
        if not entity_types or EntityType.ANATOMY in entity_types:
            for pattern, normalized in self._anatomy_patterns.items():
                for match in re.finditer(pattern, text_lower):
                    entity = self._create_entity(
                        text, match, normalized, EntityType.ANATOMY
                    )
                    extraction.entities.append(entity)

        # Detect negation for each entity
        for entity in extraction.entities:
            entity.negation_status = self._detect_negation(text, entity)

        # Calculate processing time
        extraction.processing_time_ms = (
            datetime.now(timezone.utc) - start_time
        ).total_seconds() * 1000

        return extraction

    def _create_entity(
        self,
        text: str,
        match: re.Match,
        normalized: str,
        entity_type: EntityType,
    ) -> ClinicalEntity:
        """Create a clinical entity from a regex match."""
        entity = ClinicalEntity(
            entity_id=str(uuid4()),
            entity_type=entity_type,
            text=text[match.start():match.end()],
            normalized_text=normalized,
            start_offset=match.start(),
            end_offset=match.end(),
        )

        # Add codes
        if normalized in self._snomed_mappings:
            snomed = self._snomed_mappings[normalized]
            entity.codes.append({
                "system": "http://snomed.info/sct",
                "code": snomed["code"],
                "display": snomed["display"],
            })

        if normalized in self._icd10_mappings:
            icd10 = self._icd10_mappings[normalized]
            entity.codes.append({
                "system": "http://hl7.org/fhir/sid/icd-10-cm",
                "code": icd10["code"],
                "display": icd10["display"],
            })

        return entity

    def _detect_negation(
        self,
        text: str,
        entity: ClinicalEntity,
    ) -> NegationStatus:
        """Detect if an entity is negated in context."""
        # Look at text before entity (window of 50 chars)
        window_start = max(0, entity.start_offset - 50)
        context = text[window_start:entity.start_offset].lower()

        for pattern in self._negation_patterns:
            if re.search(pattern, context):
                return NegationStatus.NEGATED

        # Check for uncertainty
        uncertainty_patterns = [r"\bpossible\b", r"\bprobable\b", r"\bsuspected\b"]
        for pattern in uncertainty_patterns:
            if re.search(pattern, context):
                return NegationStatus.UNCERTAIN

        # Check for family history
        if re.search(r"\bfamily history\b|\bfamily hx\b", context):
            return NegationStatus.FAMILY_HISTORY

        return NegationStatus.AFFIRMED

    async def suggest_codes(
        self,
        text: str,
        code_system: str = "ICD-10",
        max_suggestions: int = 5,
    ) -> List[CodingSuggestion]:
        """
        Suggest medical codes based on text.

        Args:
            text: Clinical text to analyze
            code_system: Code system (ICD-10, SNOMED, CPT)
            max_suggestions: Maximum suggestions to return

        Returns:
            List of code suggestions
        """
        suggestions = []

        # Extract entities first
        extraction = await self.extract_entities(text)

        # Generate suggestions from entities
        for entity in extraction.entities:
            if entity.negation_status == NegationStatus.NEGATED:
                continue

            for code_info in entity.codes:
                system_match = (
                    (code_system == "ICD-10" and "icd-10" in code_info["system"].lower()) or
                    (code_system == "SNOMED" and "snomed" in code_info["system"].lower())
                )

                if system_match:
                    suggestions.append(CodingSuggestion(
                        code=code_info["code"],
                        system=code_system,
                        display=code_info["display"],
                        confidence=entity.confidence,
                        evidence_text=entity.text,
                    ))

        # Deduplicate and sort by confidence
        seen = set()
        unique = []
        for s in suggestions:
            if s.code not in seen:
                seen.add(s.code)
                unique.append(s)

        unique.sort(key=lambda x: x.confidence, reverse=True)
        return unique[:max_suggestions]

    async def analyze_sentiment(
        self,
        text: str,
    ) -> SentimentResult:
        """
        Analyze sentiment of patient text.

        Useful for patient feedback and communication analysis.
        """
        text_lower = text.lower()

        # Simple keyword-based sentiment (use ML model in production)
        positive_words = ["good", "better", "great", "excellent", "happy", "satisfied", "helpful", "improved"]
        negative_words = ["bad", "worse", "terrible", "unhappy", "disappointed", "pain", "frustrated", "angry"]

        positive_count = sum(1 for w in positive_words if w in text_lower)
        negative_count = sum(1 for w in negative_words if w in text_lower)

        total = positive_count + negative_count
        if total == 0:
            sentiment = "neutral"
            score = 0.0
        elif positive_count > negative_count:
            sentiment = "positive"
            score = positive_count / total
        else:
            sentiment = "negative"
            score = -negative_count / total

        return SentimentResult(
            text=text,
            sentiment=sentiment,
            score=score,
            emotions={
                "positive": positive_count / max(total, 1),
                "negative": negative_count / max(total, 1),
            },
        )

    async def parse_sections(
        self,
        clinical_note: str,
    ) -> Dict[str, str]:
        """
        Parse a clinical note into sections.

        Identifies common sections like:
        - Chief Complaint
        - HPI
        - Physical Exam
        - Assessment
        - Plan
        """
        sections = {}

        # Common section headers
        section_patterns = [
            (r"(?:chief complaint|cc)[:\s]*(.+?)(?=\n[A-Z]|\n\n|$)", "chief_complaint"),
            (r"(?:history of present illness|hpi)[:\s]*(.+?)(?=\n[A-Z]|\n\n|$)", "hpi"),
            (r"(?:physical exam|pe|examination)[:\s]*(.+?)(?=\n[A-Z]|\n\n|$)", "physical_exam"),
            (r"(?:assessment)[:\s]*(.+?)(?=\n[A-Z]|\n\n|$)", "assessment"),
            (r"(?:plan)[:\s]*(.+?)(?=\n[A-Z]|\n\n|$)", "plan"),
            (r"(?:medications|current medications)[:\s]*(.+?)(?=\n[A-Z]|\n\n|$)", "medications"),
            (r"(?:allergies)[:\s]*(.+?)(?=\n[A-Z]|\n\n|$)", "allergies"),
            (r"(?:vitals|vital signs)[:\s]*(.+?)(?=\n[A-Z]|\n\n|$)", "vitals"),
        ]

        for pattern, section_name in section_patterns:
            match = re.search(pattern, clinical_note, re.IGNORECASE | re.DOTALL)
            if match:
                sections[section_name] = match.group(1).strip()

        return sections


# Global medical NLP service instance
medical_nlp_service = MedicalNLPService()

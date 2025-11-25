"""
Clinical NLP Pipeline

EPIC-010: Medical AI Capabilities
US-010.7: Clinical NLP Pipeline

Advanced clinical text processing:
- Section segmentation
- Problem list extraction
- Medication reconciliation
- Social determinants extraction
- Quality measure identification
- De-identification capability
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple, Set
from uuid import uuid4, UUID
import re


class SectionType(str, Enum):
    """Clinical note section types."""
    CHIEF_COMPLAINT = "chief_complaint"
    HISTORY_PRESENT_ILLNESS = "history_present_illness"
    PAST_MEDICAL_HISTORY = "past_medical_history"
    PAST_SURGICAL_HISTORY = "past_surgical_history"
    FAMILY_HISTORY = "family_history"
    SOCIAL_HISTORY = "social_history"
    REVIEW_OF_SYSTEMS = "review_of_systems"
    PHYSICAL_EXAM = "physical_exam"
    VITAL_SIGNS = "vital_signs"
    LABS_RESULTS = "labs_results"
    IMAGING = "imaging"
    ASSESSMENT = "assessment"
    PLAN = "plan"
    MEDICATIONS = "medications"
    ALLERGIES = "allergies"
    IMMUNIZATIONS = "immunizations"
    PROCEDURES = "procedures"
    HOSPITAL_COURSE = "hospital_course"
    DISCHARGE_INSTRUCTIONS = "discharge_instructions"


class SocialDeterminant(str, Enum):
    """Social determinants of health categories."""
    HOUSING = "housing"
    FOOD_SECURITY = "food_security"
    TRANSPORTATION = "transportation"
    EMPLOYMENT = "employment"
    EDUCATION = "education"
    SOCIAL_SUPPORT = "social_support"
    SUBSTANCE_USE = "substance_use"
    PHYSICAL_ACTIVITY = "physical_activity"
    STRESS = "stress"
    DOMESTIC_VIOLENCE = "domestic_violence"
    FINANCIAL_STRAIN = "financial_strain"


class QualityMeasureType(str, Enum):
    """Clinical quality measure types."""
    PREVENTIVE = "preventive"
    CHRONIC_DISEASE = "chronic_disease"
    SAFETY = "safety"
    EFFICIENCY = "efficiency"
    PATIENT_EXPERIENCE = "patient_experience"


@dataclass
class ClinicalSection:
    """Extracted clinical note section."""
    section_type: SectionType
    title: str
    content: str
    start_offset: int
    end_offset: int
    confidence: float


@dataclass
class ProblemListEntry:
    """Problem list entry."""
    problem_id: UUID
    problem_text: str
    normalized_text: str
    icd10_code: Optional[str]
    snomed_code: Optional[str]
    status: str  # active, resolved, inactive
    onset_date: Optional[str]
    is_chronic: bool
    severity: Optional[str]
    certainty: str  # confirmed, suspected, ruled_out
    source_section: SectionType


@dataclass
class MedicationEntry:
    """Medication entry for reconciliation."""
    medication_id: UUID
    medication_name: str
    generic_name: Optional[str]
    rxnorm_code: Optional[str]
    dose: Optional[str]
    frequency: Optional[str]
    route: Optional[str]
    status: str  # active, discontinued, on_hold
    start_date: Optional[str]
    end_date: Optional[str]
    prescriber: Optional[str]
    indication: Optional[str]
    source_section: SectionType
    confidence: float


@dataclass
class SocialDeterminantFinding:
    """Social determinant of health finding."""
    finding_id: UUID
    category: SocialDeterminant
    finding_text: str
    status: str  # positive, negative, unknown
    severity: Optional[str]  # mild, moderate, severe
    needs_intervention: bool
    icd10_z_code: Optional[str]
    source_section: SectionType
    confidence: float


@dataclass
class QualityMeasure:
    """Quality measure identification."""
    measure_id: str
    measure_name: str
    measure_type: QualityMeasureType
    applicable: bool
    status: str  # met, not_met, excluded
    numerator_criteria_met: List[str]
    denominator_criteria: List[str]
    exclusion_criteria: List[str]
    documentation_gaps: List[str]
    recommendations: List[str]


@dataclass
class NLPPipelineResult:
    """Complete NLP pipeline result."""
    result_id: UUID
    original_text: str

    # Sections
    sections: List[ClinicalSection]

    # Extracted data
    problem_list: List[ProblemListEntry]
    medications: List[MedicationEntry]
    allergies: List[str]
    social_determinants: List[SocialDeterminantFinding]

    # Quality measures
    quality_measures: List[QualityMeasure]

    # Summary
    clinical_summary: str
    action_items: List[str]

    # Metadata
    processing_time_ms: float
    created_at: datetime


class ClinicalSectionSplitter:
    """Split clinical notes into sections."""

    # Section header patterns
    SECTION_PATTERNS = {
        SectionType.CHIEF_COMPLAINT: [
            r'^(?:chief\s+complaint|cc|reason\s+for\s+visit|presenting\s+complaint)\s*:?',
        ],
        SectionType.HISTORY_PRESENT_ILLNESS: [
            r'^(?:history\s+of\s+present\s+illness|hpi|present\s+illness)\s*:?',
        ],
        SectionType.PAST_MEDICAL_HISTORY: [
            r'^(?:past\s+medical\s+history|pmh|medical\s+history)\s*:?',
        ],
        SectionType.PAST_SURGICAL_HISTORY: [
            r'^(?:past\s+surgical\s+history|psh|surgical\s+history)\s*:?',
        ],
        SectionType.FAMILY_HISTORY: [
            r'^(?:family\s+history|fh|fhx)\s*:?',
        ],
        SectionType.SOCIAL_HISTORY: [
            r'^(?:social\s+history|sh|shx)\s*:?',
        ],
        SectionType.REVIEW_OF_SYSTEMS: [
            r'^(?:review\s+of\s+systems|ros)\s*:?',
        ],
        SectionType.PHYSICAL_EXAM: [
            r'^(?:physical\s+exam(?:ination)?|pe|exam)\s*:?',
        ],
        SectionType.VITAL_SIGNS: [
            r'^(?:vital\s+signs?|vitals?|vs)\s*:?',
        ],
        SectionType.LABS_RESULTS: [
            r'^(?:lab(?:oratory)?\s+results?|labs?)\s*:?',
        ],
        SectionType.IMAGING: [
            r'^(?:imaging|radiology|x-?ray|ct|mri)\s*:?',
        ],
        SectionType.ASSESSMENT: [
            r'^(?:assessment|impression|diagnosis|diagnoses|dx)\s*:?',
        ],
        SectionType.PLAN: [
            r'^(?:plan|treatment\s+plan|recommendations?)\s*:?',
        ],
        SectionType.MEDICATIONS: [
            r'^(?:medications?|meds|current\s+medications?|home\s+meds?)\s*:?',
        ],
        SectionType.ALLERGIES: [
            r'^(?:allergies|drug\s+allergies|allergy)\s*:?',
        ],
        SectionType.HOSPITAL_COURSE: [
            r'^(?:hospital\s+course|course)\s*:?',
        ],
        SectionType.DISCHARGE_INSTRUCTIONS: [
            r'^(?:discharge\s+instructions?|d/c\s+instructions?)\s*:?',
        ],
    }

    def split(self, text: str) -> List[ClinicalSection]:
        """Split clinical note into sections."""
        sections = []
        lines = text.split('\n')

        current_section = None
        current_content = []
        current_start = 0

        for i, line in enumerate(lines):
            line_stripped = line.strip()

            # Check if line is a section header
            section_type = self._identify_section(line_stripped)

            if section_type:
                # Save previous section
                if current_section:
                    content = '\n'.join(current_content).strip()
                    if content:
                        sections.append(ClinicalSection(
                            section_type=current_section,
                            title=current_section.value.replace('_', ' ').title(),
                            content=content,
                            start_offset=current_start,
                            end_offset=current_start + len(content),
                            confidence=0.9
                        ))

                # Start new section
                current_section = section_type
                current_content = []
                current_start = sum(len(l) + 1 for l in lines[:i])
            else:
                if current_section:
                    current_content.append(line)

        # Save last section
        if current_section and current_content:
            content = '\n'.join(current_content).strip()
            if content:
                sections.append(ClinicalSection(
                    section_type=current_section,
                    title=current_section.value.replace('_', ' ').title(),
                    content=content,
                    start_offset=current_start,
                    end_offset=current_start + len(content),
                    confidence=0.9
                ))

        return sections

    def _identify_section(self, line: str) -> Optional[SectionType]:
        """Identify section type from line."""
        line_lower = line.lower()

        for section_type, patterns in self.SECTION_PATTERNS.items():
            for pattern in patterns:
                if re.match(pattern, line_lower, re.IGNORECASE):
                    return section_type

        return None


class ProblemListExtractor:
    """Extract problem list from clinical notes."""

    # Common condition patterns with codes
    CONDITION_PATTERNS = {
        'diabetes_type2': {
            'patterns': [r'\btype\s*2\s*diabetes\b', r'\bt2dm\b', r'\bdm\s*2\b', r'\bniddm\b'],
            'icd10': 'E11.9',
            'snomed': '44054006',
            'chronic': True
        },
        'hypertension': {
            'patterns': [r'\bhypertension\b', r'\bhtn\b', r'\bhigh\s*blood\s*pressure\b'],
            'icd10': 'I10',
            'snomed': '38341003',
            'chronic': True
        },
        'heart_failure': {
            'patterns': [r'\bheart\s*failure\b', r'\bchf\b', r'\bcongestive\s*heart\b'],
            'icd10': 'I50.9',
            'snomed': '84114007',
            'chronic': True
        },
        'copd': {
            'patterns': [r'\bcopd\b', r'\bchronic\s*obstructive\b'],
            'icd10': 'J44.9',
            'snomed': '13645005',
            'chronic': True
        },
        'asthma': {
            'patterns': [r'\basthma\b'],
            'icd10': 'J45.909',
            'snomed': '195967001',
            'chronic': True
        },
        'ckd': {
            'patterns': [r'\bckd\b', r'\bchronic\s*kidney\b', r'\bchronic\s*renal\b'],
            'icd10': 'N18.9',
            'snomed': '709044004',
            'chronic': True
        },
        'depression': {
            'patterns': [r'\bdepression\b', r'\bmdd\b', r'\bmajor\s*depressive\b'],
            'icd10': 'F32.9',
            'snomed': '35489007',
            'chronic': True
        },
        'anxiety': {
            'patterns': [r'\banxiety\b', r'\bgad\b'],
            'icd10': 'F41.9',
            'snomed': '197480006',
            'chronic': True
        },
        'hyperlipidemia': {
            'patterns': [r'\bhyperlipidemia\b', r'\bhigh\s*cholesterol\b', r'\bdyslipidemia\b'],
            'icd10': 'E78.5',
            'snomed': '55822004',
            'chronic': True
        },
        'cad': {
            'patterns': [r'\bcoronary\s*artery\s*disease\b', r'\bcad\b'],
            'icd10': 'I25.10',
            'snomed': '53741008',
            'chronic': True
        },
    }

    def extract(self, sections: List[ClinicalSection]) -> List[ProblemListEntry]:
        """Extract problem list from sections."""
        problems = []
        seen_problems = set()

        # Priority sections for problems
        priority_sections = [
            SectionType.ASSESSMENT,
            SectionType.PAST_MEDICAL_HISTORY,
            SectionType.HISTORY_PRESENT_ILLNESS
        ]

        for section in sections:
            if section.section_type in priority_sections:
                text = section.content.lower()

                for condition_key, condition_data in self.CONDITION_PATTERNS.items():
                    for pattern in condition_data['patterns']:
                        if re.search(pattern, text, re.IGNORECASE):
                            if condition_key not in seen_problems:
                                seen_problems.add(condition_key)

                                # Determine certainty based on section and context
                                certainty = 'confirmed'
                                if 'suspected' in text or 'possible' in text or 'rule out' in text:
                                    certainty = 'suspected'

                                problems.append(ProblemListEntry(
                                    problem_id=uuid4(),
                                    problem_text=condition_key.replace('_', ' ').title(),
                                    normalized_text=condition_key,
                                    icd10_code=condition_data['icd10'],
                                    snomed_code=condition_data['snomed'],
                                    status='active',
                                    onset_date=None,
                                    is_chronic=condition_data['chronic'],
                                    severity=None,
                                    certainty=certainty,
                                    source_section=section.section_type
                                ))

        return problems


class MedicationExtractor:
    """Extract and reconcile medications."""

    # Medication patterns
    MEDICATION_PATTERNS = [
        # Pattern: Drug name dose frequency route
        r'(\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml|units?))\s+((?:once|twice|three times|four times)?\s*(?:daily|bid|tid|qid|qhs|prn|as needed|q\d+h)?)',
        # Pattern: Drug name dose
        r'(\b[A-Z][a-z]+)\s+(\d+(?:\.\d+)?\s*(?:mg|mcg|g|units?))',
    ]

    # Common medication database
    MEDICATION_DB = {
        'metformin': {'rxnorm': '6809', 'generic': 'Metformin'},
        'lisinopril': {'rxnorm': '29046', 'generic': 'Lisinopril'},
        'amlodipine': {'rxnorm': '17767', 'generic': 'Amlodipine'},
        'atorvastatin': {'rxnorm': '83367', 'generic': 'Atorvastatin'},
        'metoprolol': {'rxnorm': '6918', 'generic': 'Metoprolol'},
        'omeprazole': {'rxnorm': '7646', 'generic': 'Omeprazole'},
        'gabapentin': {'rxnorm': '25480', 'generic': 'Gabapentin'},
        'sertraline': {'rxnorm': '36437', 'generic': 'Sertraline'},
        'levothyroxine': {'rxnorm': '10582', 'generic': 'Levothyroxine'},
        'aspirin': {'rxnorm': '1191', 'generic': 'Aspirin'},
        'furosemide': {'rxnorm': '4603', 'generic': 'Furosemide'},
        'prednisone': {'rxnorm': '8640', 'generic': 'Prednisone'},
        'albuterol': {'rxnorm': '435', 'generic': 'Albuterol'},
        'insulin': {'rxnorm': '5856', 'generic': 'Insulin'},
    }

    def extract(self, sections: List[ClinicalSection]) -> List[MedicationEntry]:
        """Extract medications from sections."""
        medications = []
        seen_meds = set()

        # Find medication section
        for section in sections:
            if section.section_type == SectionType.MEDICATIONS:
                meds = self._parse_medication_list(section.content)
                for med in meds:
                    if med.medication_name.lower() not in seen_meds:
                        seen_meds.add(med.medication_name.lower())
                        med.source_section = section.section_type
                        medications.append(med)

        return medications

    def _parse_medication_list(self, text: str) -> List[MedicationEntry]:
        """Parse medication list text."""
        medications = []
        lines = text.split('\n')

        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            # Remove bullet points, numbers
            line = re.sub(r'^[\d\.\-\*\•]+\s*', '', line)

            # Try to extract medication info
            med = self._parse_medication_line(line)
            if med:
                medications.append(med)

        return medications

    def _parse_medication_line(self, line: str) -> Optional[MedicationEntry]:
        """Parse a single medication line."""
        # Simple extraction - would use NER in production
        words = line.split()
        if not words:
            return None

        med_name = words[0]
        dose = None
        frequency = None

        # Look for dose
        for word in words[1:]:
            if re.match(r'\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml|units?)', word, re.I):
                dose = word
                break

        # Look for frequency
        freq_patterns = ['daily', 'bid', 'tid', 'qid', 'prn', 'qhs', 'once', 'twice']
        for word in words:
            if word.lower() in freq_patterns:
                frequency = word
                break

        # Look up in database
        med_info = self.MEDICATION_DB.get(med_name.lower(), {})

        return MedicationEntry(
            medication_id=uuid4(),
            medication_name=med_name,
            generic_name=med_info.get('generic'),
            rxnorm_code=med_info.get('rxnorm'),
            dose=dose,
            frequency=frequency,
            route='oral',  # Default
            status='active',
            start_date=None,
            end_date=None,
            prescriber=None,
            indication=None,
            source_section=SectionType.MEDICATIONS,
            confidence=0.85
        )


class SocialDeterminantsExtractor:
    """Extract social determinants of health."""

    SDOH_PATTERNS = {
        SocialDeterminant.HOUSING: {
            'positive': [r'homeless', r'housing\s*insecur', r'shelter', r'unstable\s*living', r'evict'],
            'negative': [r'stable\s*housing', r'lives\s*with\s*family', r'home\s*owner'],
            'z_code': 'Z59.0'
        },
        SocialDeterminant.FOOD_SECURITY: {
            'positive': [r'food\s*insecur', r'unable\s*to\s*afford\s*food', r'hungry', r'skipping\s*meals'],
            'negative': [r'adequate\s*nutrition', r'no\s*food\s*insecurity'],
            'z_code': 'Z59.4'
        },
        SocialDeterminant.TRANSPORTATION: {
            'positive': [r'no\s*transportation', r'transportation\s*barrier', r'cannot\s*drive', r'no\s*car'],
            'negative': [r'has\s*transportation', r'drives'],
            'z_code': 'Z59.8'
        },
        SocialDeterminant.EMPLOYMENT: {
            'positive': [r'unemploy', r'lost\s*job', r'job\s*loss', r'unable\s*to\s*work'],
            'negative': [r'employed', r'working', r'retired'],
            'z_code': 'Z56.0'
        },
        SocialDeterminant.SUBSTANCE_USE: {
            'positive': [r'alcohol\s*use', r'drinks?\s*daily', r'smok(?:es?|ing)', r'drug\s*use', r'marijuana', r'opioid'],
            'negative': [r'denies\s*(?:alcohol|tobacco|drug)', r'non-?smoker', r'quit\s*smoking'],
            'z_code': 'Z72.0'
        },
        SocialDeterminant.SOCIAL_SUPPORT: {
            'positive': [r'lives\s*alone', r'no\s*support', r'isolated', r'no\s*family\s*nearby'],
            'negative': [r'good\s*support', r'lives\s*with', r'family\s*support'],
            'z_code': 'Z60.2'
        },
        SocialDeterminant.STRESS: {
            'positive': [r'high\s*stress', r'under\s*stress', r'stressful', r'overwhelmed'],
            'negative': [r'low\s*stress', r'managing\s*stress'],
            'z_code': 'Z73.3'
        },
        SocialDeterminant.DOMESTIC_VIOLENCE: {
            'positive': [r'domestic\s*violence', r'abuse', r'intimate\s*partner', r'unsafe\s*at\s*home'],
            'negative': [r'safe\s*at\s*home', r'denies\s*abuse'],
            'z_code': 'Z63.0'
        },
    }

    def extract(self, sections: List[ClinicalSection]) -> List[SocialDeterminantFinding]:
        """Extract SDOH from sections."""
        findings = []

        # Focus on social history section
        for section in sections:
            if section.section_type == SectionType.SOCIAL_HISTORY:
                text = section.content.lower()

                for sdoh_type, patterns in self.SDOH_PATTERNS.items():
                    # Check positive patterns (problem present)
                    for pattern in patterns['positive']:
                        if re.search(pattern, text, re.IGNORECASE):
                            findings.append(SocialDeterminantFinding(
                                finding_id=uuid4(),
                                category=sdoh_type,
                                finding_text=re.search(pattern, text, re.IGNORECASE).group(),
                                status='positive',
                                severity='moderate',
                                needs_intervention=True,
                                icd10_z_code=patterns['z_code'],
                                source_section=section.section_type,
                                confidence=0.8
                            ))
                            break

        return findings


class QualityMeasureIdentifier:
    """Identify applicable quality measures."""

    QUALITY_MEASURES = {
        'diabetes_a1c': {
            'id': 'CMS122v11',
            'name': 'Diabetes: Hemoglobin A1c Poor Control (>9%)',
            'type': QualityMeasureType.CHRONIC_DISEASE,
            'denominator': ['diabetes'],
            'numerator': ['a1c > 9', 'no a1c'],
            'exclusions': ['hospice', 'pregnancy']
        },
        'diabetes_eye_exam': {
            'id': 'CMS131v10',
            'name': 'Diabetes: Eye Exam',
            'type': QualityMeasureType.CHRONIC_DISEASE,
            'denominator': ['diabetes'],
            'numerator': ['eye exam', 'retinal', 'ophthalmology'],
            'exclusions': ['hospice']
        },
        'bp_control': {
            'id': 'CMS165v10',
            'name': 'Controlling High Blood Pressure',
            'type': QualityMeasureType.CHRONIC_DISEASE,
            'denominator': ['hypertension'],
            'numerator': ['bp < 140/90', 'blood pressure controlled'],
            'exclusions': ['esrd', 'hospice', 'pregnancy']
        },
        'depression_screening': {
            'id': 'CMS2v11',
            'name': 'Preventive Care: Depression Screening',
            'type': QualityMeasureType.PREVENTIVE,
            'denominator': ['all'],
            'numerator': ['phq', 'depression screen', 'mood screen'],
            'exclusions': []
        },
        'tobacco_screening': {
            'id': 'CMS138v10',
            'name': 'Preventive Care: Tobacco Screening',
            'type': QualityMeasureType.PREVENTIVE,
            'denominator': ['all'],
            'numerator': ['tobacco', 'smoking status', 'cigarette'],
            'exclusions': []
        },
    }

    def identify(
        self,
        problem_list: List[ProblemListEntry],
        sections: List[ClinicalSection]
    ) -> List[QualityMeasure]:
        """Identify applicable quality measures."""
        measures = []

        # Convert problems to lowercase set
        problems_text = set(p.normalized_text for p in problem_list)

        # Full text for searching
        full_text = ' '.join(s.content.lower() for s in sections)

        for measure_id, measure_data in self.QUALITY_MEASURES.items():
            # Check if denominator criteria met
            applicable = False
            if 'all' in measure_data['denominator']:
                applicable = True
            else:
                applicable = any(
                    d in problems_text for d in measure_data['denominator']
                )

            if not applicable:
                continue

            # Check for exclusions
            excluded = any(
                ex in full_text for ex in measure_data['exclusions']
            )

            if excluded:
                measures.append(QualityMeasure(
                    measure_id=measure_data['id'],
                    measure_name=measure_data['name'],
                    measure_type=measure_data['type'],
                    applicable=True,
                    status='excluded',
                    numerator_criteria_met=[],
                    denominator_criteria=measure_data['denominator'],
                    exclusion_criteria=measure_data['exclusions'],
                    documentation_gaps=[],
                    recommendations=[]
                ))
                continue

            # Check numerator criteria
            numerator_met = []
            for criterion in measure_data['numerator']:
                if criterion in full_text:
                    numerator_met.append(criterion)

            # Determine status
            status = 'met' if numerator_met else 'not_met'

            # Generate recommendations
            recommendations = []
            documentation_gaps = []
            if status == 'not_met':
                documentation_gaps.append(f"Missing: {', '.join(measure_data['numerator'])}")
                recommendations.append(f"Document {measure_data['name']} compliance")

            measures.append(QualityMeasure(
                measure_id=measure_data['id'],
                measure_name=measure_data['name'],
                measure_type=measure_data['type'],
                applicable=True,
                status=status,
                numerator_criteria_met=numerator_met,
                denominator_criteria=measure_data['denominator'],
                exclusion_criteria=measure_data['exclusions'],
                documentation_gaps=documentation_gaps,
                recommendations=recommendations
            ))

        return measures


class ClinicalNLPPipeline:
    """Main clinical NLP pipeline."""

    def __init__(self):
        self.section_splitter = ClinicalSectionSplitter()
        self.problem_extractor = ProblemListExtractor()
        self.medication_extractor = MedicationExtractor()
        self.sdoh_extractor = SocialDeterminantsExtractor()
        self.quality_identifier = QualityMeasureIdentifier()

    async def process(self, clinical_text: str) -> NLPPipelineResult:
        """Process clinical text through full pipeline."""
        import time
        start_time = time.time()

        # Split into sections
        sections = self.section_splitter.split(clinical_text)

        # Extract problem list
        problem_list = self.problem_extractor.extract(sections)

        # Extract medications
        medications = self.medication_extractor.extract(sections)

        # Extract allergies
        allergies = self._extract_allergies(sections)

        # Extract social determinants
        social_determinants = self.sdoh_extractor.extract(sections)

        # Identify quality measures
        quality_measures = self.quality_identifier.identify(problem_list, sections)

        # Generate summary
        clinical_summary = self._generate_summary(
            problem_list, medications, social_determinants
        )

        # Generate action items
        action_items = self._generate_action_items(
            quality_measures, social_determinants
        )

        processing_time = (time.time() - start_time) * 1000

        return NLPPipelineResult(
            result_id=uuid4(),
            original_text=clinical_text,
            sections=sections,
            problem_list=problem_list,
            medications=medications,
            allergies=allergies,
            social_determinants=social_determinants,
            quality_measures=quality_measures,
            clinical_summary=clinical_summary,
            action_items=action_items,
            processing_time_ms=processing_time,
            created_at=datetime.now(timezone.utc)
        )

    def _extract_allergies(self, sections: List[ClinicalSection]) -> List[str]:
        """Extract allergies from sections."""
        allergies = []

        for section in sections:
            if section.section_type == SectionType.ALLERGIES:
                lines = section.content.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and not line.lower().startswith('nkda') and not line.lower().startswith('no known'):
                        # Clean up the line
                        line = re.sub(r'^[\d\.\-\*\•]+\s*', '', line)
                        if line:
                            allergies.append(line)

        if not allergies:
            # Check for NKDA
            for section in sections:
                if 'nkda' in section.content.lower() or 'no known' in section.content.lower():
                    return ['NKDA']

        return allergies

    def _generate_summary(
        self,
        problems: List[ProblemListEntry],
        medications: List[MedicationEntry],
        sdoh: List[SocialDeterminantFinding]
    ) -> str:
        """Generate clinical summary."""
        parts = []

        if problems:
            chronic = [p for p in problems if p.is_chronic]
            if chronic:
                parts.append(f"Active chronic conditions: {', '.join(p.problem_text for p in chronic[:5])}")

        if medications:
            parts.append(f"Currently on {len(medications)} medications")

        if sdoh:
            concerns = [s.category.value for s in sdoh if s.status == 'positive']
            if concerns:
                parts.append(f"SDOH concerns: {', '.join(concerns)}")

        return '. '.join(parts) if parts else "No significant findings extracted."

    def _generate_action_items(
        self,
        quality_measures: List[QualityMeasure],
        sdoh: List[SocialDeterminantFinding]
    ) -> List[str]:
        """Generate action items."""
        actions = []

        # Quality measure gaps
        for measure in quality_measures:
            if measure.status == 'not_met':
                for rec in measure.recommendations:
                    actions.append(rec)

        # SDOH interventions
        for finding in sdoh:
            if finding.needs_intervention:
                actions.append(f"Address {finding.category.value} concerns")

        return actions[:10]


# Global instance
clinical_nlp_pipeline = ClinicalNLPPipeline()

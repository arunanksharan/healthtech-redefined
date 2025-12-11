"""
Medical AI Service

Advanced AI capabilities for clinical use:
- Symptom triage and urgency assessment
- Clinical documentation suggestions
- Predictive analytics
- Risk stratification
- Treatment recommendations
- Drug interaction checking

EPIC-010: Medical AI Capabilities
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4
import logging

from .llm_service import LLMService, ChatMessage, MessageRole
from .medical_nlp import MedicalNLPService, EntityType

logger = logging.getLogger(__name__)


class UrgencyLevel(str, Enum):
    """Urgency levels for triage."""
    EMERGENCY = "emergency"     # Life-threatening, call 911
    URGENT = "urgent"          # Same-day care needed
    SOON = "soon"              # Within 24-48 hours
    ROUTINE = "routine"        # Schedule regular appointment
    SELF_CARE = "self_care"    # Can manage at home


class RiskLevel(str, Enum):
    """Risk levels for patient stratification."""
    CRITICAL = "critical"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    MINIMAL = "minimal"


class DocumentationType(str, Enum):
    """Types of clinical documentation."""
    PROGRESS_NOTE = "progress_note"
    SOAP_NOTE = "soap_note"
    PROCEDURE_NOTE = "procedure_note"
    CONSULTATION = "consultation"
    DISCHARGE_SUMMARY = "discharge_summary"
    REFERRAL_LETTER = "referral_letter"
    PRESCRIPTION = "prescription"


@dataclass
class Symptom:
    """A reported symptom with details."""
    name: str
    description: Optional[str] = None
    severity: int = 5  # 1-10
    duration: Optional[str] = None  # "2 days", "1 week", etc.
    onset: Optional[str] = None  # "sudden", "gradual"
    location: Optional[str] = None
    character: Optional[str] = None  # "sharp", "dull", "throbbing"
    aggravating_factors: List[str] = field(default_factory=list)
    relieving_factors: List[str] = field(default_factory=list)
    associated_symptoms: List[str] = field(default_factory=list)


@dataclass
class SymptomAnalysis:
    """
    Analysis of patient symptoms.

    Provides clinical insights without diagnosis.
    """
    analysis_id: str
    timestamp: datetime

    # Input
    symptoms: List[Symptom]
    patient_age: Optional[int] = None
    patient_sex: Optional[str] = None
    medical_history: List[str] = field(default_factory=list)
    current_medications: List[str] = field(default_factory=list)

    # Analysis
    primary_concerns: List[str] = field(default_factory=list)
    possible_conditions: List[Dict[str, Any]] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)
    red_flags: List[str] = field(default_factory=list)  # Warning signs

    # Recommendations
    recommended_actions: List[str] = field(default_factory=list)
    questions_to_ask: List[str] = field(default_factory=list)
    tests_to_consider: List[str] = field(default_factory=list)

    # Confidence
    confidence_score: float = 0.0  # 0-1

    # Disclaimer
    disclaimer: str = (
        "This analysis is for informational purposes only and does not "
        "constitute medical advice, diagnosis, or treatment. Please consult "
        "a healthcare provider for medical concerns."
    )


@dataclass
class TriageResult:
    """
    Result of symptom triage assessment.

    Determines urgency level for seeking care.
    """
    triage_id: str
    timestamp: datetime

    # Assessment
    urgency_level: UrgencyLevel
    urgency_score: int  # 1-100, higher = more urgent

    # Reasoning
    primary_concern: str
    contributing_factors: List[str] = field(default_factory=list)
    red_flags_identified: List[str] = field(default_factory=list)

    # Recommendations
    recommended_action: str  # What to do next
    timeframe: str  # "immediately", "within 24 hours", etc.
    care_setting: str  # "emergency room", "urgent care", "primary care", "home"

    # Additional guidance
    self_care_advice: List[str] = field(default_factory=list)
    warning_signs: List[str] = field(default_factory=list)  # Watch for these

    # Confidence
    confidence_score: float = 0.0

    # Safety
    disclaimer: str = (
        "This triage assessment is for guidance only. If you believe you are "
        "experiencing a medical emergency, please call 911 or go to the nearest "
        "emergency room immediately."
    )


@dataclass
class DocumentationSuggestion:
    """
    AI-generated documentation suggestion.

    Assists providers with clinical documentation.
    """
    suggestion_id: str
    timestamp: datetime
    documentation_type: DocumentationType

    # Generated content
    suggested_text: str
    sections: Dict[str, str] = field(default_factory=dict)  # Section name -> content

    # Extracted information
    extracted_codes: List[Dict[str, str]] = field(default_factory=list)  # ICD-10, CPT
    extracted_medications: List[str] = field(default_factory=list)
    extracted_diagnoses: List[str] = field(default_factory=list)

    # Metadata
    source_input: str = ""  # What was used to generate this
    confidence_score: float = 0.0
    requires_review: bool = True

    # Provider should always review
    disclaimer: str = (
        "This is an AI-generated suggestion. Provider review and approval "
        "is required before use in the medical record."
    )


@dataclass
class RiskAssessment:
    """Patient risk assessment result."""
    assessment_id: str
    patient_id: str
    timestamp: datetime

    # Risk levels
    overall_risk: RiskLevel
    risk_score: int  # 0-100

    # Risk factors
    risk_factors: List[Dict[str, Any]] = field(default_factory=list)
    protective_factors: List[str] = field(default_factory=list)

    # Specific risks
    hospitalization_risk: float = 0.0  # 30-day
    readmission_risk: float = 0.0  # 30-day
    fall_risk: float = 0.0
    medication_nonadherence_risk: float = 0.0

    # Recommendations
    interventions: List[str] = field(default_factory=list)
    monitoring_recommendations: List[str] = field(default_factory=list)

    # Model info
    model_version: str = "1.0"
    confidence_interval: Tuple[float, float] = (0.0, 0.0)


@dataclass
class DrugInteraction:
    """Drug-drug interaction alert."""
    interaction_id: str
    drug_a: str
    drug_b: str
    severity: str  # "major", "moderate", "minor"
    description: str
    mechanism: Optional[str] = None
    management: Optional[str] = None
    references: List[str] = field(default_factory=list)


@dataclass
class TreatmentSuggestion:
    """AI-suggested treatment option."""
    suggestion_id: str
    condition: str
    treatment_type: str  # "medication", "procedure", "lifestyle", "referral"

    # Suggestion
    suggestion: str
    rationale: str

    # Evidence
    evidence_level: str  # "high", "moderate", "low"
    guidelines_reference: Optional[str] = None

    # Considerations
    contraindications: List[str] = field(default_factory=list)
    precautions: List[str] = field(default_factory=list)
    alternatives: List[str] = field(default_factory=list)

    # Always requires clinical judgment
    requires_clinical_review: bool = True


class MedicalAIService:
    """
    Medical AI service for clinical decision support.

    Provides AI-powered medical capabilities including:
    - Symptom triage
    - Documentation assistance
    - Risk stratification
    - Drug interaction checking
    - Treatment suggestions
    """

    def __init__(
        self,
        llm_service: Optional[LLMService] = None,
        nlp_service: Optional[MedicalNLPService] = None,
    ):
        self.llm_service = llm_service or LLMService()
        self.nlp_service = nlp_service or MedicalNLPService()

        # Red flag symptoms database
        self._red_flags = self._load_red_flags()

        # Drug interaction database (simplified)
        self._drug_interactions = self._load_drug_interactions()

    def _load_red_flags(self) -> Dict[str, List[str]]:
        """Load red flag symptoms by body system."""
        return {
            "neurological": [
                "sudden severe headache",
                "vision changes",
                "weakness on one side",
                "difficulty speaking",
                "confusion",
                "seizure",
                "loss of consciousness",
            ],
            "cardiac": [
                "chest pain",
                "shortness of breath",
                "palpitations with dizziness",
                "leg swelling",
                "arm pain radiating",
            ],
            "respiratory": [
                "difficulty breathing",
                "coughing blood",
                "severe wheezing",
                "blue lips",
            ],
            "gastrointestinal": [
                "vomiting blood",
                "blood in stool",
                "severe abdominal pain",
                "inability to keep fluids down",
            ],
            "infectious": [
                "high fever over 103°F",
                "stiff neck with fever",
                "rash with fever",
            ],
            "mental_health": [
                "suicidal thoughts",
                "self-harm",
                "psychotic symptoms",
            ],
        }

    def _load_drug_interactions(self) -> List[Dict[str, Any]]:
        """Load drug interaction database."""
        # Simplified database - in production, use comprehensive database
        return [
            {
                "drug_a": "warfarin",
                "drug_b": "aspirin",
                "severity": "major",
                "description": "Increased risk of bleeding when used together",
                "management": "Monitor closely for signs of bleeding. Consider alternative antiplatelet if possible.",
            },
            {
                "drug_a": "metformin",
                "drug_b": "contrast dye",
                "severity": "major",
                "description": "Risk of lactic acidosis with iodinated contrast",
                "management": "Hold metformin 48 hours before and after contrast administration.",
            },
            {
                "drug_a": "ssri",
                "drug_b": "maoi",
                "severity": "major",
                "description": "Risk of serotonin syndrome",
                "management": "Contraindicated. Allow washout period between medications.",
            },
            {
                "drug_a": "ace_inhibitor",
                "drug_b": "potassium",
                "severity": "moderate",
                "description": "Risk of hyperkalemia",
                "management": "Monitor potassium levels regularly.",
            },
            {
                "drug_a": "statin",
                "drug_b": "grapefruit",
                "severity": "moderate",
                "description": "Grapefruit increases statin levels",
                "management": "Avoid grapefruit or use pravastatin/rosuvastatin which have less interaction.",
            },
        ]

    async def analyze_symptoms(
        self,
        symptoms: List[Symptom],
        patient_age: Optional[int] = None,
        patient_sex: Optional[str] = None,
        medical_history: Optional[List[str]] = None,
        current_medications: Optional[List[str]] = None,
    ) -> SymptomAnalysis:
        """
        Analyze patient symptoms.

        Provides clinical insights without making diagnoses.

        Args:
            symptoms: List of reported symptoms
            patient_age: Patient's age
            patient_sex: Patient's sex (M/F)
            medical_history: Relevant medical history
            current_medications: Current medications

        Returns:
            SymptomAnalysis with insights and recommendations
        """
        analysis = SymptomAnalysis(
            analysis_id=str(uuid4()),
            timestamp=datetime.now(timezone.utc),
            symptoms=symptoms,
            patient_age=patient_age,
            patient_sex=patient_sex,
            medical_history=medical_history or [],
            current_medications=current_medications or [],
        )

        # Check for red flags
        red_flags = self._identify_red_flags(symptoms)
        analysis.red_flags = red_flags

        # Identify primary concerns
        analysis.primary_concerns = self._identify_primary_concerns(symptoms)

        # Identify risk factors
        analysis.risk_factors = self._identify_risk_factors(
            patient_age, patient_sex, medical_history or []
        )

        # Generate recommendations
        analysis.recommended_actions = self._generate_recommendations(
            symptoms, red_flags
        )

        # Suggest follow-up questions
        analysis.questions_to_ask = self._generate_followup_questions(symptoms)

        # Suggest tests to consider
        analysis.tests_to_consider = self._suggest_tests(symptoms)

        # Calculate confidence
        analysis.confidence_score = self._calculate_confidence(symptoms)

        # Use LLM for possible conditions (informational only)
        possible_conditions = await self._get_possible_conditions(
            symptoms, patient_age, patient_sex, medical_history
        )
        analysis.possible_conditions = possible_conditions

        logger.info(
            f"Completed symptom analysis {analysis.analysis_id}, "
            f"red_flags: {len(red_flags)}, "
            f"confidence: {analysis.confidence_score:.2f}"
        )

        return analysis

    def _identify_red_flags(self, symptoms: List[Symptom]) -> List[str]:
        """Identify red flag symptoms requiring immediate attention."""
        red_flags = []

        for symptom in symptoms:
            symptom_text = f"{symptom.name} {symptom.description or ''}".lower()

            for system, flags in self._red_flags.items():
                for flag in flags:
                    if flag.lower() in symptom_text:
                        red_flags.append(f"{flag} ({system})")

            # High severity is a red flag
            if symptom.severity >= 9:
                red_flags.append(f"Severe {symptom.name} (severity {symptom.severity}/10)")

        return list(set(red_flags))

    def _identify_primary_concerns(self, symptoms: List[Symptom]) -> List[str]:
        """Identify primary clinical concerns."""
        concerns = []

        # Sort by severity
        sorted_symptoms = sorted(symptoms, key=lambda s: s.severity, reverse=True)

        for symptom in sorted_symptoms[:3]:  # Top 3
            concern = f"{symptom.name}"
            if symptom.duration:
                concern += f" for {symptom.duration}"
            if symptom.severity >= 7:
                concern += " (severe)"
            concerns.append(concern)

        return concerns

    def _identify_risk_factors(
        self,
        age: Optional[int],
        sex: Optional[str],
        medical_history: List[str],
    ) -> List[str]:
        """Identify patient risk factors."""
        risk_factors = []

        if age:
            if age >= 65:
                risk_factors.append("Age 65 or older")
            if age < 2:
                risk_factors.append("Infant/toddler age")

        history_lower = [h.lower() for h in medical_history]

        chronic_conditions = [
            ("diabetes", "Diabetes"),
            ("heart disease", "Heart disease"),
            ("hypertension", "Hypertension"),
            ("copd", "COPD"),
            ("asthma", "Asthma"),
            ("immunocompromised", "Immunocompromised"),
            ("cancer", "Cancer history"),
        ]

        for condition, label in chronic_conditions:
            if any(condition in h for h in history_lower):
                risk_factors.append(label)

        return risk_factors

    def _generate_recommendations(
        self,
        symptoms: List[Symptom],
        red_flags: List[str],
    ) -> List[str]:
        """Generate recommended actions."""
        recommendations = []

        if red_flags:
            recommendations.append(
                "Seek immediate medical attention due to concerning symptoms"
            )

        max_severity = max(s.severity for s in symptoms) if symptoms else 0

        if max_severity >= 8:
            recommendations.append("Consider urgent care or emergency room visit")
        elif max_severity >= 6:
            recommendations.append("Schedule an appointment within 24-48 hours")
        else:
            recommendations.append("Monitor symptoms and schedule routine appointment if persisting")

        # General recommendations
        recommendations.extend([
            "Keep track of symptom changes",
            "Note any new symptoms that develop",
            "Stay hydrated and rest",
        ])

        return recommendations

    def _generate_followup_questions(
        self,
        symptoms: List[Symptom],
    ) -> List[str]:
        """Generate follow-up questions for assessment."""
        questions = []

        for symptom in symptoms:
            if not symptom.duration:
                questions.append(f"How long have you had {symptom.name}?")
            if not symptom.onset:
                questions.append(f"Did the {symptom.name} come on suddenly or gradually?")
            if not symptom.aggravating_factors:
                questions.append(f"What makes the {symptom.name} worse?")
            if not symptom.relieving_factors:
                questions.append(f"What helps relieve the {symptom.name}?")

        # General questions
        if len(questions) < 5:
            general_questions = [
                "Have you had any recent illnesses or infections?",
                "Have there been any changes in your medications?",
                "Are you experiencing any other symptoms?",
                "Have you traveled recently?",
            ]
            questions.extend(general_questions[:5 - len(questions)])

        return questions[:5]

    def _suggest_tests(self, symptoms: List[Symptom]) -> List[str]:
        """Suggest diagnostic tests to consider."""
        tests = []
        symptom_names = [s.name.lower() for s in symptoms]

        # Symptom-based test suggestions
        if any("chest" in s or "heart" in s for s in symptom_names):
            tests.extend(["ECG", "Cardiac enzymes", "Chest X-ray"])

        if any("fever" in s or "infection" in s for s in symptom_names):
            tests.extend(["Complete blood count", "Basic metabolic panel"])

        if any("headache" in s for s in symptom_names):
            tests.extend(["Neurological exam", "Consider imaging if red flags"])

        if any("abdominal" in s or "stomach" in s for s in symptom_names):
            tests.extend(["Abdominal exam", "Consider ultrasound or CT if indicated"])

        return list(set(tests))[:5]

    def _calculate_confidence(self, symptoms: List[Symptom]) -> float:
        """Calculate confidence in the analysis."""
        # More detailed symptoms = higher confidence
        base_confidence = 0.5

        for symptom in symptoms:
            if symptom.duration:
                base_confidence += 0.05
            if symptom.severity:
                base_confidence += 0.03
            if symptom.onset:
                base_confidence += 0.02
            if symptom.associated_symptoms:
                base_confidence += 0.05

        return min(0.95, base_confidence)

    async def _get_possible_conditions(
        self,
        symptoms: List[Symptom],
        age: Optional[int],
        sex: Optional[str],
        medical_history: Optional[List[str]],
    ) -> List[Dict[str, Any]]:
        """Use LLM to suggest possible conditions (informational only)."""
        # Build prompt
        symptom_text = "\n".join([
            f"- {s.name}: severity {s.severity}/10, duration: {s.duration or 'unknown'}"
            for s in symptoms
        ])

        messages = [
            ChatMessage(
                role=MessageRole.SYSTEM,
                content="""You are a medical information assistant. Based on symptoms,
provide possible conditions for educational purposes only. This is NOT a diagnosis.
Always recommend consulting a healthcare provider.

For each possible condition, provide:
- Condition name
- Why it might match (brief)
- Likelihood (high/medium/low)

Limit to top 3 most relevant possibilities.""",
            ),
            ChatMessage(
                role=MessageRole.USER,
                content=f"""Patient info:
- Age: {age or 'unknown'}
- Sex: {sex or 'unknown'}
- Medical history: {', '.join(medical_history or ['none provided'])}

Symptoms:
{symptom_text}

What are possible conditions to consider (for educational purposes)?""",
            ),
        ]

        try:
            completion = await self.llm_service.complete(
                messages=messages,
                temperature=0.3,
                max_tokens=500,
            )

            # Parse response into structured format
            # In production, use structured output parsing
            return [{
                "description": completion.message.content,
                "disclaimer": "For educational purposes only. Not a diagnosis.",
            }]
        except Exception as e:
            logger.error(f"Error getting possible conditions: {e}")
            return []

    async def triage_symptoms(
        self,
        symptoms: List[Symptom],
        patient_age: Optional[int] = None,
        patient_sex: Optional[str] = None,
        medical_history: Optional[List[str]] = None,
    ) -> TriageResult:
        """
        Perform symptom triage to determine urgency.

        Args:
            symptoms: List of reported symptoms
            patient_age: Patient's age
            patient_sex: Patient's sex
            medical_history: Relevant medical history

        Returns:
            TriageResult with urgency level and recommendations
        """
        # First analyze symptoms
        analysis = await self.analyze_symptoms(
            symptoms, patient_age, patient_sex, medical_history
        )

        # Determine urgency based on red flags and severity
        urgency_level, urgency_score = self._calculate_urgency(
            symptoms, analysis.red_flags, patient_age, medical_history
        )

        # Get care recommendations
        care_setting, timeframe = self._get_care_recommendations(urgency_level)

        # Build triage result
        triage = TriageResult(
            triage_id=str(uuid4()),
            timestamp=datetime.now(timezone.utc),
            urgency_level=urgency_level,
            urgency_score=urgency_score,
            primary_concern=analysis.primary_concerns[0] if analysis.primary_concerns else "Multiple symptoms",
            contributing_factors=analysis.risk_factors,
            red_flags_identified=analysis.red_flags,
            recommended_action=self._get_action_recommendation(urgency_level),
            timeframe=timeframe,
            care_setting=care_setting,
            self_care_advice=self._get_self_care_advice(symptoms, urgency_level),
            warning_signs=self._get_warning_signs(symptoms),
            confidence_score=analysis.confidence_score,
        )

        logger.info(
            f"Completed triage {triage.triage_id}, "
            f"urgency: {urgency_level.value}, "
            f"score: {urgency_score}"
        )

        return triage

    def _calculate_urgency(
        self,
        symptoms: List[Symptom],
        red_flags: List[str],
        age: Optional[int],
        medical_history: Optional[List[str]],
    ) -> Tuple[UrgencyLevel, int]:
        """Calculate urgency level and score."""
        score = 0

        # Red flags are most important
        score += len(red_flags) * 20

        # Symptom severity
        max_severity = max(s.severity for s in symptoms) if symptoms else 0
        score += max_severity * 5

        # Age considerations
        if age:
            if age < 2 or age > 75:
                score += 15

        # Medical history
        if medical_history:
            high_risk_conditions = ["diabetes", "heart", "cancer", "immunocompromised"]
            for condition in high_risk_conditions:
                if any(condition in h.lower() for h in medical_history):
                    score += 10

        # Determine level
        if score >= 80 or any("emergency" in rf.lower() for rf in red_flags):
            return UrgencyLevel.EMERGENCY, min(100, score)
        elif score >= 60:
            return UrgencyLevel.URGENT, score
        elif score >= 40:
            return UrgencyLevel.SOON, score
        elif score >= 20:
            return UrgencyLevel.ROUTINE, score
        else:
            return UrgencyLevel.SELF_CARE, score

    def _get_care_recommendations(
        self,
        urgency: UrgencyLevel,
    ) -> Tuple[str, str]:
        """Get care setting and timeframe recommendations."""
        recommendations = {
            UrgencyLevel.EMERGENCY: ("Emergency room", "Immediately"),
            UrgencyLevel.URGENT: ("Urgent care or same-day appointment", "Within 4 hours"),
            UrgencyLevel.SOON: ("Primary care office", "Within 24-48 hours"),
            UrgencyLevel.ROUTINE: ("Primary care office", "Within 1-2 weeks"),
            UrgencyLevel.SELF_CARE: ("Home self-care", "Monitor and follow up if needed"),
        }
        return recommendations.get(urgency, ("Primary care", "As appropriate"))

    def _get_action_recommendation(self, urgency: UrgencyLevel) -> str:
        """Get action recommendation based on urgency."""
        actions = {
            UrgencyLevel.EMERGENCY: (
                "Call 911 or go to the nearest emergency room immediately. "
                "Do not drive yourself."
            ),
            UrgencyLevel.URGENT: (
                "Seek medical care today. Visit urgent care or contact your "
                "healthcare provider for a same-day appointment."
            ),
            UrgencyLevel.SOON: (
                "Schedule an appointment with your healthcare provider within "
                "the next day or two."
            ),
            UrgencyLevel.ROUTINE: (
                "Schedule a regular appointment with your healthcare provider "
                "to discuss your symptoms."
            ),
            UrgencyLevel.SELF_CARE: (
                "Your symptoms can likely be managed at home. Monitor your "
                "condition and seek care if symptoms worsen."
            ),
        }
        return actions.get(urgency, "Consult your healthcare provider.")

    def _get_self_care_advice(
        self,
        symptoms: List[Symptom],
        urgency: UrgencyLevel,
    ) -> List[str]:
        """Get self-care advice based on symptoms."""
        advice = []

        if urgency in [UrgencyLevel.EMERGENCY, UrgencyLevel.URGENT]:
            return ["Seek medical care as recommended above."]

        # General advice
        advice.extend([
            "Get adequate rest",
            "Stay well hydrated",
            "Monitor temperature if fever is present",
        ])

        # Symptom-specific
        symptom_names = [s.name.lower() for s in symptoms]

        if any("pain" in s for s in symptom_names):
            advice.append("Over-the-counter pain relievers may help (follow package directions)")

        if any("fever" in s for s in symptom_names):
            advice.append("Use fever reducers as directed, apply cool compresses")

        if any("cough" in s or "cold" in s for s in symptom_names):
            advice.append("Use a humidifier, try warm fluids, honey for cough (if over 1 year old)")

        return advice

    def _get_warning_signs(self, symptoms: List[Symptom]) -> List[str]:
        """Get warning signs to watch for."""
        return [
            "Sudden worsening of symptoms",
            "High fever (over 103°F)",
            "Difficulty breathing or shortness of breath",
            "Severe or worsening pain",
            "New confusion or difficulty staying awake",
            "Signs of dehydration (dark urine, dizziness)",
            "Symptoms not improving after expected time",
        ]

    async def generate_documentation(
        self,
        documentation_type: DocumentationType,
        clinical_input: str,
        patient_context: Optional[Dict[str, Any]] = None,
    ) -> DocumentationSuggestion:
        """
        Generate documentation suggestion based on clinical input.

        Args:
            documentation_type: Type of documentation to generate
            clinical_input: Clinical information (transcription, notes, etc.)
            patient_context: Additional patient context

        Returns:
            DocumentationSuggestion with generated content
        """
        # Extract entities from clinical input
        entities = await self.nlp_service.extract_entities(
            clinical_input,
            [EntityType.CONDITION, EntityType.SYMPTOM, EntityType.MEDICATION, EntityType.PROCEDURE],
        )

        # Get code suggestions
        icd_codes = await self.nlp_service.suggest_codes(clinical_input, "icd10", 5)
        cpt_codes = await self.nlp_service.suggest_codes(clinical_input, "cpt", 3)

        # Build prompt for documentation
        system_prompt = self._get_documentation_system_prompt(documentation_type)

        messages = [
            ChatMessage(role=MessageRole.SYSTEM, content=system_prompt),
            ChatMessage(
                role=MessageRole.USER,
                content=f"""Generate a {documentation_type.value} based on the following information:

Clinical Input:
{clinical_input}

Patient Context:
{patient_context or 'No additional context provided'}

Please generate appropriate clinical documentation.""",
            ),
        ]

        try:
            completion = await self.llm_service.complete(
                messages=messages,
                temperature=0.3,
                max_tokens=1500,
            )

            # Parse sections from the response
            sections = await self.nlp_service.parse_sections(completion.message.content)

            suggestion = DocumentationSuggestion(
                suggestion_id=str(uuid4()),
                timestamp=datetime.now(timezone.utc),
                documentation_type=documentation_type,
                suggested_text=completion.message.content,
                sections=sections,
                extracted_codes=[
                    {"system": "ICD-10", "code": c.code, "display": c.display}
                    for c in icd_codes
                ] + [
                    {"system": "CPT", "code": c.code, "display": c.display}
                    for c in cpt_codes
                ],
                extracted_medications=[
                    e.text for e in entities.entities
                    if e.entity_type == EntityType.MEDICATION
                ],
                extracted_diagnoses=[
                    e.text for e in entities.entities
                    if e.entity_type == EntityType.CONDITION
                ],
                source_input=clinical_input[:500],  # Truncate for storage
                confidence_score=0.75,  # Base confidence for LLM-generated content
            )

            logger.info(
                f"Generated documentation {suggestion.suggestion_id}, "
                f"type: {documentation_type.value}"
            )

            return suggestion

        except Exception as e:
            logger.error(f"Error generating documentation: {e}")
            raise

    def _get_documentation_system_prompt(
        self,
        doc_type: DocumentationType,
    ) -> str:
        """Get system prompt for documentation type."""
        prompts = {
            DocumentationType.SOAP_NOTE: """You are a clinical documentation assistant.
Generate a SOAP note with the following sections:
- Subjective: Patient's reported symptoms and history
- Objective: Examination findings, vitals, test results
- Assessment: Clinical impression and diagnoses
- Plan: Treatment plan and follow-up

Use proper medical terminology. Be concise but thorough.""",

            DocumentationType.PROGRESS_NOTE: """You are a clinical documentation assistant.
Generate a progress note documenting the patient visit.
Include relevant history, current status, changes noted,
and plan going forward. Use appropriate medical terminology.""",

            DocumentationType.DISCHARGE_SUMMARY: """You are a clinical documentation assistant.
Generate a discharge summary including:
- Admission diagnosis and reason
- Hospital course
- Procedures performed
- Discharge diagnosis
- Discharge medications
- Follow-up instructions

Be comprehensive but organized.""",

            DocumentationType.REFERRAL_LETTER: """You are a clinical documentation assistant.
Generate a referral letter including:
- Patient demographics
- Reason for referral
- Relevant history
- Current medications
- Specific questions for the specialist

Be professional and concise.""",
        }

        return prompts.get(
            doc_type,
            "You are a clinical documentation assistant. Generate appropriate medical documentation based on the input provided."
        )

    async def check_drug_interactions(
        self,
        medications: List[str],
    ) -> List[DrugInteraction]:
        """
        Check for drug-drug interactions.

        Args:
            medications: List of medication names

        Returns:
            List of identified drug interactions
        """
        interactions = []

        # Normalize medication names
        meds_lower = [m.lower() for m in medications]

        # Check against interaction database
        for interaction in self._drug_interactions:
            drug_a = interaction["drug_a"].lower()
            drug_b = interaction["drug_b"].lower()

            # Check if both drugs are in the list
            has_drug_a = any(drug_a in m for m in meds_lower)
            has_drug_b = any(drug_b in m for m in meds_lower)

            if has_drug_a and has_drug_b:
                interactions.append(DrugInteraction(
                    interaction_id=str(uuid4()),
                    drug_a=interaction["drug_a"],
                    drug_b=interaction["drug_b"],
                    severity=interaction["severity"],
                    description=interaction["description"],
                    management=interaction.get("management"),
                ))

        logger.info(f"Checked {len(medications)} medications, found {len(interactions)} interactions")
        return interactions

    async def assess_patient_risk(
        self,
        patient_id: str,
        demographics: Dict[str, Any],
        diagnoses: List[str],
        medications: List[str],
        vitals: Optional[Dict[str, Any]] = None,
        lab_results: Optional[List[Dict[str, Any]]] = None,
    ) -> RiskAssessment:
        """
        Assess patient risk for adverse outcomes.

        Args:
            patient_id: Patient identifier
            demographics: Age, sex, etc.
            diagnoses: Active diagnoses
            medications: Current medications
            vitals: Recent vital signs
            lab_results: Recent lab results

        Returns:
            RiskAssessment with stratification
        """
        risk_factors = []
        protective_factors = []
        risk_score = 0

        # Age risk
        age = demographics.get("age", 0)
        if age >= 75:
            risk_factors.append({"factor": "Age 75+", "weight": 15})
            risk_score += 15
        elif age >= 65:
            risk_factors.append({"factor": "Age 65-74", "weight": 10})
            risk_score += 10

        # Diagnosis-based risk
        high_risk_diagnoses = {
            "heart failure": 20,
            "copd": 15,
            "diabetes": 10,
            "chronic kidney disease": 15,
            "cancer": 20,
        }

        for diagnosis in diagnoses:
            diag_lower = diagnosis.lower()
            for condition, weight in high_risk_diagnoses.items():
                if condition in diag_lower:
                    risk_factors.append({"factor": condition.title(), "weight": weight})
                    risk_score += weight

        # Polypharmacy risk
        if len(medications) >= 10:
            risk_factors.append({"factor": "Polypharmacy (10+ medications)", "weight": 15})
            risk_score += 15
        elif len(medications) >= 5:
            risk_factors.append({"factor": "Multiple medications (5-9)", "weight": 8})
            risk_score += 8

        # Protective factors
        if demographics.get("has_caregiver"):
            protective_factors.append("Has caregiver support")
            risk_score -= 5

        if demographics.get("active_lifestyle"):
            protective_factors.append("Active lifestyle")
            risk_score -= 5

        # Determine overall risk level
        risk_score = max(0, min(100, risk_score))

        if risk_score >= 70:
            overall_risk = RiskLevel.CRITICAL
        elif risk_score >= 50:
            overall_risk = RiskLevel.HIGH
        elif risk_score >= 30:
            overall_risk = RiskLevel.MODERATE
        elif risk_score >= 15:
            overall_risk = RiskLevel.LOW
        else:
            overall_risk = RiskLevel.MINIMAL

        # Generate interventions
        interventions = self._generate_interventions(overall_risk, risk_factors)

        assessment = RiskAssessment(
            assessment_id=str(uuid4()),
            patient_id=patient_id,
            timestamp=datetime.now(timezone.utc),
            overall_risk=overall_risk,
            risk_score=risk_score,
            risk_factors=risk_factors,
            protective_factors=protective_factors,
            hospitalization_risk=risk_score / 100 * 0.3,  # Simplified calculation
            readmission_risk=risk_score / 100 * 0.25,
            interventions=interventions,
            monitoring_recommendations=self._get_monitoring_recommendations(overall_risk),
            confidence_interval=(max(0, risk_score - 10), min(100, risk_score + 10)),
        )

        logger.info(
            f"Risk assessment for patient {patient_id}: "
            f"{overall_risk.value} (score: {risk_score})"
        )

        return assessment

    def _generate_interventions(
        self,
        risk_level: RiskLevel,
        risk_factors: List[Dict[str, Any]],
    ) -> List[str]:
        """Generate recommended interventions based on risk."""
        interventions = []

        if risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
            interventions.extend([
                "Schedule care management enrollment",
                "Consider home health assessment",
                "Medication reconciliation review",
                "Establish advanced care planning discussion",
            ])

        if risk_level == RiskLevel.MODERATE:
            interventions.extend([
                "Schedule follow-up within 2 weeks",
                "Review medication adherence",
                "Assess social support needs",
            ])

        # Factor-specific interventions
        factor_names = [f["factor"].lower() for f in risk_factors]

        if any("heart failure" in f for f in factor_names):
            interventions.append("Daily weight monitoring")
            interventions.append("Fluid restriction education")

        if any("diabetes" in f for f in factor_names):
            interventions.append("Diabetes education referral")
            interventions.append("HbA1c monitoring")

        if any("polypharmacy" in f or "medication" in f for f in factor_names):
            interventions.append("Pharmacist medication review")
            interventions.append("Deprescribing assessment")

        return list(set(interventions))

    def _get_monitoring_recommendations(
        self,
        risk_level: RiskLevel,
    ) -> List[str]:
        """Get monitoring recommendations based on risk level."""
        base_recommendations = [
            "Regular vital sign monitoring",
            "Symptom tracking",
        ]

        if risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
            base_recommendations.extend([
                "Weekly phone check-ins",
                "Monthly in-person visits",
                "Remote patient monitoring if available",
                "24-hour nurse line access",
            ])
        elif risk_level == RiskLevel.MODERATE:
            base_recommendations.extend([
                "Monthly phone check-ins",
                "Quarterly visits",
            ])

        return base_recommendations


# Global medical AI service instance
medical_ai_service = MedicalAIService()

"""
Clinical Documentation AI Service

EPIC-010: Medical AI Capabilities
US-010.2: Clinical Documentation AI

AI-assisted clinical documentation including:
- Ambient listening and transcription
- Automatic SOAP note generation
- ICD-10/CPT code suggestions
- Template customization
- Medical terminology accuracy
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from uuid import uuid4, UUID
import re


class DocumentationType(str, Enum):
    """Clinical documentation types."""
    SOAP_NOTE = "soap_note"
    PROGRESS_NOTE = "progress_note"
    HISTORY_PHYSICAL = "history_physical"
    CONSULTATION = "consultation"
    PROCEDURE_NOTE = "procedure_note"
    DISCHARGE_SUMMARY = "discharge_summary"
    REFERRAL_LETTER = "referral_letter"
    PRESCRIPTION = "prescription"
    LAB_ORDER = "lab_order"
    IMAGING_ORDER = "imaging_order"
    OPERATIVE_REPORT = "operative_report"
    ADMISSION_NOTE = "admission_note"


class SectionType(str, Enum):
    """Clinical note section types."""
    CHIEF_COMPLAINT = "chief_complaint"
    HISTORY_PRESENT_ILLNESS = "history_present_illness"
    PAST_MEDICAL_HISTORY = "past_medical_history"
    PAST_SURGICAL_HISTORY = "past_surgical_history"
    MEDICATIONS = "medications"
    ALLERGIES = "allergies"
    FAMILY_HISTORY = "family_history"
    SOCIAL_HISTORY = "social_history"
    REVIEW_OF_SYSTEMS = "review_of_systems"
    PHYSICAL_EXAM = "physical_exam"
    VITAL_SIGNS = "vital_signs"
    ASSESSMENT = "assessment"
    PLAN = "plan"
    ORDERS = "orders"
    FOLLOW_UP = "follow_up"
    ATTESTATION = "attestation"


@dataclass
class TranscriptionSegment:
    """Segment of transcribed speech."""
    speaker: str  # "provider", "patient", "other"
    text: str
    start_time: float
    end_time: float
    confidence: float
    is_medical_term: bool = False


@dataclass
class ExtractedCodeSuggestion:
    """Suggested medical code."""
    code: str
    system: str  # ICD-10, CPT, SNOMED, etc.
    display: str
    confidence: float
    evidence_text: str
    section_source: str
    specificity_level: str  # "billable", "header", "unspecified"
    hcc_relevant: bool = False


@dataclass
class DocumentationSection:
    """Generated documentation section."""
    section_type: SectionType
    title: str
    content: str
    source_segments: List[int]  # Indices into transcription
    confidence: float
    suggested_codes: List[ExtractedCodeSuggestion]
    requires_review: bool = False
    review_reason: Optional[str] = None


@dataclass
class GeneratedDocumentation:
    """Complete generated clinical documentation."""
    document_id: UUID
    documentation_type: DocumentationType
    encounter_id: Optional[UUID]
    patient_id: Optional[UUID]

    # Content
    sections: Dict[SectionType, DocumentationSection]
    full_text: str
    template_used: Optional[str]

    # Coding
    icd10_suggestions: List[ExtractedCodeSuggestion]
    cpt_suggestions: List[ExtractedCodeSuggestion]
    hcc_captures: List[ExtractedCodeSuggestion]

    # Quality
    completeness_score: float
    accuracy_confidence: float
    documentation_quality_score: float

    # Review
    requires_provider_review: bool
    review_areas: List[str]
    missing_elements: List[str]

    # Compliance
    attestation_required: bool
    signature_status: str

    # Metadata
    created_at: datetime
    version: int = 1


class AmbientTranscriptionService:
    """Process ambient audio from clinical encounters."""

    # Medical terminology patterns for enhanced recognition
    MEDICAL_TERM_PATTERNS = [
        r'\b(diagnos\w*|symptom\w*|prescrib\w*|medicat\w*|treat\w*)\b',
        r'\b(\d+\s*mg|\d+\s*ml|\d+\s*units?)\b',
        r'\b(twice|three times|once)\s*(daily|a day|per day)\b',
        r'\b(blood pressure|heart rate|temperature|oxygen|pulse)\b',
        r'\b(diabetes|hypertension|asthma|copd|heart disease)\b',
    ]

    # Speaker identification patterns
    PROVIDER_PATTERNS = [
        r"(let me|I'm going to|we'll|I recommend|the plan is|I think)",
        r"(your (test|labs?|results?|x-?ray))",
        r"(take this|prescrib\w*|refer\w*)",
    ]

    PATIENT_PATTERNS = [
        r"(I feel|I've been|it hurts|my \w+ (is|are|has))",
        r"(I'm worried|I'm concerned|I noticed)",
        r"(how long|when should|what if)",
    ]

    async def transcribe_audio(
        self,
        audio_data: bytes,
        format: str = "wav",
        sample_rate: int = 16000
    ) -> List[TranscriptionSegment]:
        """
        Transcribe audio with speaker diarization.

        In production, this would integrate with:
        - Whisper for transcription
        - Speaker diarization models
        - Medical speech recognition fine-tuning
        """
        # Mock implementation - would use actual ASR
        segments = []

        # Simulated transcription result
        mock_transcription = [
            {"speaker": "patient", "text": "I've been having this chest pain for about two days.",
             "start": 0.0, "end": 3.5, "confidence": 0.95},
            {"speaker": "provider", "text": "Can you describe the pain? Is it sharp or dull?",
             "start": 4.0, "end": 6.5, "confidence": 0.97},
            {"speaker": "patient", "text": "It's more of a pressure feeling, especially when I walk upstairs.",
             "start": 7.0, "end": 11.0, "confidence": 0.94},
            {"speaker": "provider", "text": "And do you have any shortness of breath with it?",
             "start": 11.5, "end": 14.0, "confidence": 0.96},
        ]

        for i, seg in enumerate(mock_transcription):
            is_medical = any(
                re.search(pattern, seg["text"], re.IGNORECASE)
                for pattern in self.MEDICAL_TERM_PATTERNS
            )
            segments.append(TranscriptionSegment(
                speaker=seg["speaker"],
                text=seg["text"],
                start_time=seg["start"],
                end_time=seg["end"],
                confidence=seg["confidence"],
                is_medical_term=is_medical
            ))

        return segments

    def identify_speaker(self, text: str) -> str:
        """Identify likely speaker based on content patterns."""
        text_lower = text.lower()

        provider_score = sum(
            1 for p in self.PROVIDER_PATTERNS
            if re.search(p, text_lower)
        )

        patient_score = sum(
            1 for p in self.PATIENT_PATTERNS
            if re.search(p, text_lower)
        )

        if provider_score > patient_score:
            return "provider"
        elif patient_score > provider_score:
            return "patient"
        return "unknown"


class SOAPNoteGenerator:
    """Generate SOAP notes from clinical encounter data."""

    def __init__(self):
        self.code_suggester = MedicalCodeSuggester()

    async def generate_soap_note(
        self,
        transcription: List[TranscriptionSegment],
        patient_context: Optional[Dict[str, Any]] = None,
        encounter_context: Optional[Dict[str, Any]] = None,
        template: Optional[str] = None
    ) -> GeneratedDocumentation:
        """Generate a complete SOAP note from transcription."""

        # Extract relevant information from transcription
        patient_statements = [s for s in transcription if s.speaker == "patient"]
        provider_statements = [s for s in transcription if s.speaker == "provider"]
        full_text = ' '.join(s.text for s in transcription)

        # Generate each section
        sections = {}

        # Subjective section
        sections[SectionType.CHIEF_COMPLAINT] = self._generate_chief_complaint(
            patient_statements, patient_context
        )
        sections[SectionType.HISTORY_PRESENT_ILLNESS] = self._generate_hpi(
            patient_statements, full_text
        )

        # Add history sections if context available
        if patient_context:
            if patient_context.get('medical_history'):
                sections[SectionType.PAST_MEDICAL_HISTORY] = self._format_pmh(
                    patient_context['medical_history']
                )
            if patient_context.get('medications'):
                sections[SectionType.MEDICATIONS] = self._format_medications(
                    patient_context['medications']
                )
            if patient_context.get('allergies'):
                sections[SectionType.ALLERGIES] = self._format_allergies(
                    patient_context['allergies']
                )

        # Objective section
        sections[SectionType.PHYSICAL_EXAM] = self._generate_physical_exam(
            provider_statements, encounter_context
        )
        if encounter_context and encounter_context.get('vitals'):
            sections[SectionType.VITAL_SIGNS] = self._format_vitals(
                encounter_context['vitals']
            )

        # Assessment
        sections[SectionType.ASSESSMENT] = self._generate_assessment(
            full_text, patient_context
        )

        # Plan
        sections[SectionType.PLAN] = self._generate_plan(
            provider_statements, full_text
        )

        # Generate code suggestions
        icd10_codes = self.code_suggester.suggest_icd10(full_text, sections)
        cpt_codes = self.code_suggester.suggest_cpt(sections, encounter_context)
        hcc_captures = self.code_suggester.identify_hcc_opportunities(icd10_codes)

        # Calculate quality metrics
        completeness = self._calculate_completeness(sections)
        accuracy = self._estimate_accuracy(sections, transcription)
        quality = (completeness + accuracy) / 2

        # Identify review areas
        review_areas = self._identify_review_areas(sections, icd10_codes)
        missing = self._identify_missing_elements(sections)

        # Generate full text
        full_note = self._compile_full_note(sections)

        return GeneratedDocumentation(
            document_id=uuid4(),
            documentation_type=DocumentationType.SOAP_NOTE,
            encounter_id=encounter_context.get('encounter_id') if encounter_context else None,
            patient_id=patient_context.get('patient_id') if patient_context else None,
            sections=sections,
            full_text=full_note,
            template_used=template,
            icd10_suggestions=icd10_codes,
            cpt_suggestions=cpt_codes,
            hcc_captures=hcc_captures,
            completeness_score=completeness,
            accuracy_confidence=accuracy,
            documentation_quality_score=quality,
            requires_provider_review=len(review_areas) > 0 or quality < 0.8,
            review_areas=review_areas,
            missing_elements=missing,
            attestation_required=True,
            signature_status="pending",
            created_at=datetime.now(timezone.utc)
        )

    def _generate_chief_complaint(
        self,
        patient_statements: List[TranscriptionSegment],
        context: Optional[Dict]
    ) -> DocumentationSection:
        """Extract chief complaint from patient statements."""
        if not patient_statements:
            return DocumentationSection(
                section_type=SectionType.CHIEF_COMPLAINT,
                title="Chief Complaint",
                content="[To be documented]",
                source_segments=[],
                confidence=0.0,
                suggested_codes=[],
                requires_review=True,
                review_reason="No patient statements found"
            )

        # Extract the primary complaint
        first_statement = patient_statements[0].text
        cc = self._extract_chief_complaint(first_statement)

        return DocumentationSection(
            section_type=SectionType.CHIEF_COMPLAINT,
            title="Chief Complaint",
            content=cc,
            source_segments=[0],
            confidence=patient_statements[0].confidence,
            suggested_codes=[],
            requires_review=False
        )

    def _extract_chief_complaint(self, text: str) -> str:
        """Extract concise chief complaint from statement."""
        # Common patterns for chief complaints
        patterns = [
            r"(?:I've been having|I have|I'm experiencing)\s+(.+?)(?:\.|,|for)",
            r"(?:problem with|trouble with)\s+(.+?)(?:\.|,|$)",
            r"(.+?)\s+(?:is bothering|hurts|pain)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip().capitalize()

        # If no pattern matches, use first part of text
        return text.split('.')[0].strip()[:100]

    def _generate_hpi(
        self,
        patient_statements: List[TranscriptionSegment],
        full_text: str
    ) -> DocumentationSection:
        """Generate History of Present Illness."""
        if not patient_statements:
            return DocumentationSection(
                section_type=SectionType.HISTORY_PRESENT_ILLNESS,
                title="History of Present Illness",
                content="[To be documented]",
                source_segments=[],
                confidence=0.0,
                suggested_codes=[],
                requires_review=True
            )

        # Extract HPI elements
        elements = {
            'onset': self._extract_onset(full_text),
            'location': self._extract_location(full_text),
            'duration': self._extract_duration(full_text),
            'character': self._extract_character(full_text),
            'aggravating': self._extract_aggravating(full_text),
            'relieving': self._extract_relieving(full_text),
            'timing': self._extract_timing(full_text),
            'severity': self._extract_severity(full_text),
        }

        # Generate narrative HPI
        narrative = self._compose_hpi_narrative(elements, patient_statements)

        return DocumentationSection(
            section_type=SectionType.HISTORY_PRESENT_ILLNESS,
            title="History of Present Illness",
            content=narrative,
            source_segments=list(range(len(patient_statements))),
            confidence=0.85,
            suggested_codes=[],
            requires_review=len(patient_statements) < 2
        )

    def _extract_onset(self, text: str) -> Optional[str]:
        """Extract onset timing."""
        patterns = [
            r'(?:started|began|first noticed)\s+(.+?(?:ago|yesterday|today|week|month|day))',
            r'for\s+(about\s+)?(\d+\s+(?:day|week|month|hour)s?)',
            r'(sudden(?:ly)?|gradual(?:ly)?)\s+(?:onset|started)',
        ]
        for p in patterns:
            match = re.search(p, text, re.IGNORECASE)
            if match:
                return match.group(0)
        return None

    def _extract_location(self, text: str) -> Optional[str]:
        """Extract symptom location."""
        body_parts = [
            'head', 'chest', 'abdomen', 'back', 'neck', 'throat', 'arm', 'leg',
            'shoulder', 'knee', 'hip', 'wrist', 'ankle', 'stomach', 'heart'
        ]
        for part in body_parts:
            if part in text.lower():
                return part
        return None

    def _extract_duration(self, text: str) -> Optional[str]:
        """Extract duration."""
        match = re.search(r'for\s+(?:about\s+)?(\d+\s+(?:day|week|month|hour|minute)s?)', text, re.I)
        if match:
            return match.group(1)
        return None

    def _extract_character(self, text: str) -> Optional[str]:
        """Extract character of symptoms."""
        characters = ['sharp', 'dull', 'aching', 'burning', 'pressure', 'throbbing', 'cramping']
        for char in characters:
            if char in text.lower():
                return char
        return None

    def _extract_aggravating(self, text: str) -> Optional[str]:
        """Extract aggravating factors."""
        patterns = [
            r'(?:worse|worsens|aggravated)\s+(?:when|with|by)\s+(.+?)(?:\.|,|$)',
            r'(?:when I|if I)\s+(.+?),?\s+(?:it gets worse|it hurts more)',
        ]
        for p in patterns:
            match = re.search(p, text, re.I)
            if match:
                return match.group(1)
        return None

    def _extract_relieving(self, text: str) -> Optional[str]:
        """Extract relieving factors."""
        patterns = [
            r'(?:better|improves|relieved)\s+(?:when|with|by)\s+(.+?)(?:\.|,|$)',
            r'(?:rest|medication|ice|heat)\s+(?:helps|makes it better)',
        ]
        for p in patterns:
            match = re.search(p, text, re.I)
            if match:
                return match.group(1)
        return None

    def _extract_timing(self, text: str) -> Optional[str]:
        """Extract timing patterns."""
        patterns = [
            r'(?:constant|intermittent|comes and goes)',
            r'(?:morning|evening|night|afternoon)',
            r'(?:after (?:eating|exercise|sleep))',
        ]
        for p in patterns:
            match = re.search(p, text, re.I)
            if match:
                return match.group(0)
        return None

    def _extract_severity(self, text: str) -> Optional[str]:
        """Extract severity."""
        patterns = [
            r'(\d+)\s*(?:out of|\/)\s*10',
            r'(mild|moderate|severe|worst)',
        ]
        for p in patterns:
            match = re.search(p, text, re.I)
            if match:
                return match.group(0)
        return None

    def _compose_hpi_narrative(
        self,
        elements: Dict[str, Optional[str]],
        statements: List[TranscriptionSegment]
    ) -> str:
        """Compose HPI narrative from extracted elements."""
        parts = []

        # Opening with chief complaint context
        if statements:
            parts.append(f"Patient presents with {statements[0].text.lower()}")

        # Add elements in logical order
        if elements['onset']:
            parts.append(f"Onset: {elements['onset']}.")
        if elements['duration']:
            parts.append(f"Duration: {elements['duration']}.")
        if elements['location']:
            parts.append(f"Location: {elements['location']}.")
        if elements['character']:
            parts.append(f"Character: {elements['character']}.")
        if elements['severity']:
            parts.append(f"Severity: {elements['severity']}.")
        if elements['aggravating']:
            parts.append(f"Aggravating factors: {elements['aggravating']}.")
        if elements['relieving']:
            parts.append(f"Relieving factors: {elements['relieving']}.")
        if elements['timing']:
            parts.append(f"Timing: {elements['timing']}.")

        return ' '.join(parts) if parts else "[History of present illness to be documented]"

    def _format_pmh(self, history: List[str]) -> DocumentationSection:
        """Format past medical history."""
        content = '\n'.join(f"- {h}" for h in history) if history else "No significant PMH reported"

        return DocumentationSection(
            section_type=SectionType.PAST_MEDICAL_HISTORY,
            title="Past Medical History",
            content=content,
            source_segments=[],
            confidence=0.95,
            suggested_codes=[],
            requires_review=False
        )

    def _format_medications(self, medications: List[Dict]) -> DocumentationSection:
        """Format current medications."""
        lines = []
        for med in medications:
            if isinstance(med, dict):
                name = med.get('name', 'Unknown')
                dose = med.get('dose', '')
                freq = med.get('frequency', '')
                lines.append(f"- {name} {dose} {freq}".strip())
            else:
                lines.append(f"- {med}")

        content = '\n'.join(lines) if lines else "No current medications"

        return DocumentationSection(
            section_type=SectionType.MEDICATIONS,
            title="Current Medications",
            content=content,
            source_segments=[],
            confidence=0.95,
            suggested_codes=[],
            requires_review=False
        )

    def _format_allergies(self, allergies: List[str]) -> DocumentationSection:
        """Format allergies."""
        content = '\n'.join(f"- {a}" for a in allergies) if allergies else "NKDA (No Known Drug Allergies)"

        return DocumentationSection(
            section_type=SectionType.ALLERGIES,
            title="Allergies",
            content=content,
            source_segments=[],
            confidence=0.95,
            suggested_codes=[],
            requires_review=False
        )

    def _generate_physical_exam(
        self,
        provider_statements: List[TranscriptionSegment],
        encounter_context: Optional[Dict]
    ) -> DocumentationSection:
        """Generate physical exam section."""
        # Extract exam findings from provider statements
        exam_findings = []

        if encounter_context and encounter_context.get('exam_findings'):
            exam_findings = encounter_context['exam_findings']
        else:
            # Try to extract from transcription
            for statement in provider_statements:
                if any(term in statement.text.lower() for term in
                      ['exam', 'look', 'feel', 'sound', 'appear']):
                    exam_findings.append(statement.text)

        if not exam_findings:
            content = "[Physical examination findings to be documented]"
            requires_review = True
        else:
            content = '\n'.join(f"- {f}" for f in exam_findings)
            requires_review = False

        return DocumentationSection(
            section_type=SectionType.PHYSICAL_EXAM,
            title="Physical Examination",
            content=content,
            source_segments=[],
            confidence=0.7 if exam_findings else 0.0,
            suggested_codes=[],
            requires_review=requires_review
        )

    def _format_vitals(self, vitals: Dict) -> DocumentationSection:
        """Format vital signs."""
        lines = []

        if vitals.get('temperature'):
            lines.append(f"Temperature: {vitals['temperature']}°F")
        if vitals.get('blood_pressure') or (vitals.get('systolic') and vitals.get('diastolic')):
            bp = vitals.get('blood_pressure') or f"{vitals['systolic']}/{vitals['diastolic']}"
            lines.append(f"Blood Pressure: {bp} mmHg")
        if vitals.get('heart_rate') or vitals.get('pulse'):
            hr = vitals.get('heart_rate') or vitals.get('pulse')
            lines.append(f"Heart Rate: {hr} bpm")
        if vitals.get('respiratory_rate'):
            lines.append(f"Respiratory Rate: {vitals['respiratory_rate']} breaths/min")
        if vitals.get('oxygen_saturation') or vitals.get('spo2'):
            spo2 = vitals.get('oxygen_saturation') or vitals.get('spo2')
            lines.append(f"Oxygen Saturation: {spo2}%")
        if vitals.get('weight'):
            lines.append(f"Weight: {vitals['weight']}")
        if vitals.get('height'):
            lines.append(f"Height: {vitals['height']}")

        content = '\n'.join(lines) if lines else "Vital signs to be documented"

        return DocumentationSection(
            section_type=SectionType.VITAL_SIGNS,
            title="Vital Signs",
            content=content,
            source_segments=[],
            confidence=0.99,
            suggested_codes=[],
            requires_review=False
        )

    def _generate_assessment(
        self,
        full_text: str,
        patient_context: Optional[Dict]
    ) -> DocumentationSection:
        """Generate assessment section."""
        # In production, this would use LLM for differential diagnosis
        # For now, extract key findings

        findings = []

        # Extract conditions mentioned
        condition_patterns = [
            r'(?:suggests?|consistent with|concerning for|likely)\s+(\w+(?:\s+\w+)?)',
            r'(?:rule out|r/o)\s+(\w+(?:\s+\w+)?)',
        ]

        for pattern in condition_patterns:
            matches = re.findall(pattern, full_text, re.I)
            findings.extend(matches)

        if not findings:
            content = "[Assessment to be documented by provider]"
            requires_review = True
        else:
            content = '\n'.join(f"1. {f.capitalize()}" for f in findings[:5])
            requires_review = True  # Assessment always needs review

        return DocumentationSection(
            section_type=SectionType.ASSESSMENT,
            title="Assessment",
            content=content,
            source_segments=[],
            confidence=0.6,
            suggested_codes=[],
            requires_review=requires_review,
            review_reason="Assessment requires provider verification"
        )

    def _generate_plan(
        self,
        provider_statements: List[TranscriptionSegment],
        full_text: str
    ) -> DocumentationSection:
        """Generate plan section."""
        plan_items = []

        # Extract plan items from provider statements
        plan_keywords = ['will', 'order', 'prescribe', 'refer', 'schedule', 'recommend',
                        'return', 'follow up', 'call if']

        for statement in provider_statements:
            if any(kw in statement.text.lower() for kw in plan_keywords):
                plan_items.append(statement.text)

        if not plan_items:
            content = "[Treatment plan to be documented]"
            requires_review = True
        else:
            content = '\n'.join(f"- {p}" for p in plan_items)
            requires_review = True

        return DocumentationSection(
            section_type=SectionType.PLAN,
            title="Plan",
            content=content,
            source_segments=[],
            confidence=0.7 if plan_items else 0.0,
            suggested_codes=[],
            requires_review=requires_review,
            review_reason="Plan requires provider verification"
        )

    def _calculate_completeness(self, sections: Dict[SectionType, DocumentationSection]) -> float:
        """Calculate documentation completeness score."""
        required_sections = [
            SectionType.CHIEF_COMPLAINT,
            SectionType.HISTORY_PRESENT_ILLNESS,
            SectionType.PHYSICAL_EXAM,
            SectionType.ASSESSMENT,
            SectionType.PLAN
        ]

        present = sum(
            1 for s in required_sections
            if s in sections and sections[s].content and
            not sections[s].content.startswith('[')
        )

        return present / len(required_sections)

    def _estimate_accuracy(
        self,
        sections: Dict[SectionType, DocumentationSection],
        transcription: List[TranscriptionSegment]
    ) -> float:
        """Estimate accuracy based on confidence scores."""
        if not sections:
            return 0.0

        confidences = [s.confidence for s in sections.values()]
        return sum(confidences) / len(confidences)

    def _identify_review_areas(
        self,
        sections: Dict[SectionType, DocumentationSection],
        codes: List[ExtractedCodeSuggestion]
    ) -> List[str]:
        """Identify areas requiring provider review."""
        review_areas = []

        for section in sections.values():
            if section.requires_review:
                review_areas.append(f"{section.title}: {section.review_reason or 'Review required'}")

        # Check for low confidence codes
        low_conf_codes = [c for c in codes if c.confidence < 0.7]
        if low_conf_codes:
            review_areas.append(f"Verify suggested codes: {', '.join(c.code for c in low_conf_codes)}")

        return review_areas

    def _identify_missing_elements(
        self,
        sections: Dict[SectionType, DocumentationSection]
    ) -> List[str]:
        """Identify missing documentation elements."""
        missing = []

        required = {
            SectionType.CHIEF_COMPLAINT: "Chief complaint",
            SectionType.HISTORY_PRESENT_ILLNESS: "History of present illness",
            SectionType.PHYSICAL_EXAM: "Physical examination",
            SectionType.ASSESSMENT: "Assessment/diagnosis",
            SectionType.PLAN: "Treatment plan"
        }

        for section_type, name in required.items():
            if section_type not in sections:
                missing.append(name)
            elif sections[section_type].content.startswith('['):
                missing.append(name)

        return missing

    def _compile_full_note(
        self,
        sections: Dict[SectionType, DocumentationSection]
    ) -> str:
        """Compile all sections into full note text."""
        note_parts = []

        # Order of sections
        section_order = [
            SectionType.CHIEF_COMPLAINT,
            SectionType.HISTORY_PRESENT_ILLNESS,
            SectionType.PAST_MEDICAL_HISTORY,
            SectionType.PAST_SURGICAL_HISTORY,
            SectionType.MEDICATIONS,
            SectionType.ALLERGIES,
            SectionType.FAMILY_HISTORY,
            SectionType.SOCIAL_HISTORY,
            SectionType.REVIEW_OF_SYSTEMS,
            SectionType.VITAL_SIGNS,
            SectionType.PHYSICAL_EXAM,
            SectionType.ASSESSMENT,
            SectionType.PLAN,
            SectionType.FOLLOW_UP
        ]

        for section_type in section_order:
            if section_type in sections:
                section = sections[section_type]
                note_parts.append(f"**{section.title}**\n{section.content}\n")

        return '\n'.join(note_parts)


class MedicalCodeSuggester:
    """Suggest ICD-10 and CPT codes from documentation."""

    # ICD-10 code mappings
    ICD10_PATTERNS = {
        'I10': ('Essential hypertension', ['hypertension', 'high blood pressure', 'htn']),
        'E11.9': ('Type 2 diabetes mellitus without complications', ['diabetes', 'diabetic', 'dm2']),
        'J06.9': ('Acute upper respiratory infection', ['uri', 'upper respiratory', 'cold', 'sore throat']),
        'R51.9': ('Headache, unspecified', ['headache', 'head pain']),
        'M54.5': ('Low back pain', ['low back pain', 'lbp', 'lumbar pain']),
        'R10.9': ('Unspecified abdominal pain', ['abdominal pain', 'stomach pain']),
        'J20.9': ('Acute bronchitis, unspecified', ['bronchitis', 'chest cold']),
        'R05.9': ('Cough, unspecified', ['cough', 'coughing']),
        'R50.9': ('Fever, unspecified', ['fever', 'febrile']),
        'N39.0': ('Urinary tract infection', ['uti', 'urinary infection', 'bladder infection']),
        'J02.9': ('Acute pharyngitis, unspecified', ['pharyngitis', 'sore throat']),
        'H10.9': ('Conjunctivitis, unspecified', ['pink eye', 'conjunctivitis', 'eye infection']),
        'K21.0': ('GERD with esophagitis', ['gerd', 'acid reflux', 'heartburn']),
        'F41.9': ('Anxiety disorder, unspecified', ['anxiety', 'anxious']),
        'F32.9': ('Major depressive disorder', ['depression', 'depressed']),
        'G43.909': ('Migraine, unspecified', ['migraine']),
        'I25.10': ('Coronary artery disease', ['cad', 'coronary disease']),
        'J45.909': ('Asthma, unspecified', ['asthma', 'asthmatic']),
        'M79.3': ('Panniculitis, unspecified', ['pain']),
    }

    # CPT code mappings for E/M services
    CPT_EM_CODES = {
        '99211': ('Office visit, minimal', 5),
        '99212': ('Office visit, straightforward', 10),
        '99213': ('Office visit, low complexity', 15),
        '99214': ('Office visit, moderate complexity', 25),
        '99215': ('Office visit, high complexity', 40),
        '99201': ('New patient, straightforward', 10),
        '99202': ('New patient, low complexity', 20),
        '99203': ('New patient, moderate complexity', 30),
        '99204': ('New patient, moderate-high complexity', 45),
        '99205': ('New patient, high complexity', 60),
    }

    # HCC (Hierarchical Condition Category) relevant codes
    HCC_CODES = {
        'E11.9': 19,   # Diabetes without complications
        'E11.65': 18,  # Diabetes with hyperglycemia
        'I50.9': 85,   # Heart failure
        'J44.9': 111,  # COPD
        'N18.3': 138,  # CKD stage 3
        'F32.9': 59,   # Depression
        'I25.10': 86,  # CAD
    }

    def suggest_icd10(
        self,
        text: str,
        sections: Dict[SectionType, DocumentationSection]
    ) -> List[ExtractedCodeSuggestion]:
        """Suggest ICD-10 codes from documentation."""
        suggestions = []
        text_lower = text.lower()

        # Check assessment section first
        assessment_text = ""
        if SectionType.ASSESSMENT in sections:
            assessment_text = sections[SectionType.ASSESSMENT].content.lower()

        for code, (display, keywords) in self.ICD10_PATTERNS.items():
            matched_keywords = [kw for kw in keywords if kw in text_lower or kw in assessment_text]
            if matched_keywords:
                # Higher confidence if in assessment
                confidence = 0.85 if any(kw in assessment_text for kw in keywords) else 0.7

                suggestions.append(ExtractedCodeSuggestion(
                    code=code,
                    system="ICD-10-CM",
                    display=display,
                    confidence=confidence,
                    evidence_text=f"Keyword match: {', '.join(matched_keywords)}",
                    section_source="assessment" if assessment_text else "full_text",
                    specificity_level="billable",
                    hcc_relevant=code in self.HCC_CODES
                ))

        # Sort by confidence
        suggestions.sort(key=lambda x: x.confidence, reverse=True)
        return suggestions[:10]

    def suggest_cpt(
        self,
        sections: Dict[SectionType, DocumentationSection],
        encounter_context: Optional[Dict]
    ) -> List[ExtractedCodeSuggestion]:
        """Suggest CPT codes based on documentation."""
        suggestions = []

        # Determine visit complexity for E/M coding
        complexity_score = self._calculate_visit_complexity(sections, encounter_context)

        # Suggest E/M code based on complexity
        if encounter_context and encounter_context.get('is_new_patient'):
            if complexity_score >= 45:
                code = '99205'
            elif complexity_score >= 30:
                code = '99204'
            elif complexity_score >= 20:
                code = '99203'
            elif complexity_score >= 10:
                code = '99202'
            else:
                code = '99201'
        else:
            if complexity_score >= 40:
                code = '99215'
            elif complexity_score >= 25:
                code = '99214'
            elif complexity_score >= 15:
                code = '99213'
            elif complexity_score >= 10:
                code = '99212'
            else:
                code = '99211'

        display, _ = self.CPT_EM_CODES[code]

        suggestions.append(ExtractedCodeSuggestion(
            code=code,
            system="CPT",
            display=display,
            confidence=0.8,
            evidence_text=f"Complexity score: {complexity_score}",
            section_source="calculated",
            specificity_level="billable",
            hcc_relevant=False
        ))

        return suggestions

    def _calculate_visit_complexity(
        self,
        sections: Dict[SectionType, DocumentationSection],
        context: Optional[Dict]
    ) -> int:
        """Calculate visit complexity score for E/M coding."""
        score = 0

        # Check HPI elements (OLDCARTS)
        if SectionType.HISTORY_PRESENT_ILLNESS in sections:
            hpi = sections[SectionType.HISTORY_PRESENT_ILLNESS].content.lower()
            hpi_elements = ['onset', 'location', 'duration', 'character',
                          'aggravating', 'relieving', 'timing', 'severity']
            element_count = sum(1 for e in hpi_elements if e in hpi)
            score += min(element_count * 2, 16)

        # Check review of systems
        if SectionType.REVIEW_OF_SYSTEMS in sections:
            score += 8

        # Check exam elements
        if SectionType.PHYSICAL_EXAM in sections:
            exam = sections[SectionType.PHYSICAL_EXAM].content
            if exam and not exam.startswith('['):
                exam_systems = exam.count('-')
                score += min(exam_systems * 2, 12)

        # Check medical decision making
        if SectionType.ASSESSMENT in sections:
            assessment = sections[SectionType.ASSESSMENT].content
            diagnosis_count = assessment.count('\n') + 1
            score += min(diagnosis_count * 4, 16)

        if SectionType.PLAN in sections:
            plan = sections[SectionType.PLAN].content
            plan_items = plan.count('-') + plan.count('\n')
            score += min(plan_items * 2, 8)

        return score

    def identify_hcc_opportunities(
        self,
        icd10_codes: List[ExtractedCodeSuggestion]
    ) -> List[ExtractedCodeSuggestion]:
        """Identify HCC capture opportunities."""
        hcc_captures = []

        for suggestion in icd10_codes:
            if suggestion.code in self.HCC_CODES:
                hcc_captures.append(ExtractedCodeSuggestion(
                    code=suggestion.code,
                    system="HCC",
                    display=f"HCC {self.HCC_CODES[suggestion.code]}: {suggestion.display}",
                    confidence=suggestion.confidence,
                    evidence_text=suggestion.evidence_text,
                    section_source=suggestion.section_source,
                    specificity_level="hcc_capture",
                    hcc_relevant=True
                ))

        return hcc_captures


class DocumentationTemplateEngine:
    """Manage and apply documentation templates."""

    TEMPLATES = {
        'soap_default': {
            'name': 'Standard SOAP Note',
            'sections': [
                SectionType.CHIEF_COMPLAINT,
                SectionType.HISTORY_PRESENT_ILLNESS,
                SectionType.PAST_MEDICAL_HISTORY,
                SectionType.MEDICATIONS,
                SectionType.ALLERGIES,
                SectionType.VITAL_SIGNS,
                SectionType.PHYSICAL_EXAM,
                SectionType.ASSESSMENT,
                SectionType.PLAN
            ]
        },
        'progress_note': {
            'name': 'Progress Note',
            'sections': [
                SectionType.CHIEF_COMPLAINT,
                SectionType.VITAL_SIGNS,
                SectionType.PHYSICAL_EXAM,
                SectionType.ASSESSMENT,
                SectionType.PLAN
            ]
        },
        'procedure_note': {
            'name': 'Procedure Note',
            'sections': [
                SectionType.CHIEF_COMPLAINT,
                SectionType.VITAL_SIGNS,
                SectionType.ASSESSMENT,
                SectionType.PLAN
            ]
        }
    }

    def get_template(self, template_name: str) -> Optional[Dict]:
        """Get a documentation template."""
        return self.TEMPLATES.get(template_name)

    def list_templates(self) -> List[Dict[str, str]]:
        """List available templates."""
        return [
            {'id': k, 'name': v['name']}
            for k, v in self.TEMPLATES.items()
        ]


# Global instances
ambient_transcription_service = AmbientTranscriptionService()
soap_generator = SOAPNoteGenerator()
code_suggester = MedicalCodeSuggester()
template_engine = DocumentationTemplateEngine()

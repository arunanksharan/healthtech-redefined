"""
Clinical Documentation System

Comprehensive clinical documentation including:
- SOAP note templates
- Progress notes
- History and physical
- Procedure documentation
- Smart phrases and macros
- Voice dictation support
- Auto-coding suggestions

EPIC-006: US-006.5 Clinical Documentation
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4
import logging
import re

logger = logging.getLogger(__name__)


class NoteStatus(str, Enum):
    """Clinical note status."""
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    PENDING_SIGNATURE = "pending_signature"
    SIGNED = "signed"
    COSIGNED = "cosigned"
    AMENDED = "amended"
    ADDENDUM = "addendum"


class NoteType(str, Enum):
    """Types of clinical notes."""
    PROGRESS_NOTE = "progress_note"
    HISTORY_PHYSICAL = "history_physical"
    CONSULTATION = "consultation"
    PROCEDURE_NOTE = "procedure_note"
    OPERATIVE_NOTE = "operative_note"
    DISCHARGE_SUMMARY = "discharge_summary"
    NURSING_NOTE = "nursing_note"
    TELEPHONE_ENCOUNTER = "telephone_encounter"
    TELEMEDICINE = "telemedicine"


@dataclass
class SOAPNote:
    """SOAP (Subjective, Objective, Assessment, Plan) note structure."""
    subjective: str = ""
    # Chief complaint, history of present illness, review of systems
    chief_complaint: str = ""
    hpi: str = ""
    ros: Dict[str, str] = field(default_factory=dict)

    objective: str = ""
    # Physical exam, vitals, diagnostic results
    vitals: Dict[str, Any] = field(default_factory=dict)
    physical_exam: Dict[str, str] = field(default_factory=dict)
    diagnostic_results: List[str] = field(default_factory=list)

    assessment: str = ""
    # Diagnoses, differential diagnoses
    diagnoses: List[Dict[str, str]] = field(default_factory=list)
    differential: List[str] = field(default_factory=list)

    plan: str = ""
    # Treatment plan items
    plan_items: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class SmartPhrase:
    """Reusable text snippet/macro."""
    phrase_id: str
    tenant_id: str
    owner_id: Optional[str]  # None = shared, otherwise user-specific

    abbreviation: str  # e.g., ".normalexam"
    name: str
    content: str
    category: str = ""

    # Variable placeholders in content
    variables: List[str] = field(default_factory=list)

    is_active: bool = True
    usage_count: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class NoteTemplate:
    """Clinical note template."""
    template_id: str
    tenant_id: str

    name: str
    note_type: NoteType
    specialty: Optional[str] = None

    # Template structure
    sections: List[Dict[str, Any]] = field(default_factory=list)
    default_content: Dict[str, str] = field(default_factory=dict)

    # Smart phrases included
    smart_phrases: List[str] = field(default_factory=list)

    is_default: bool = False
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ClinicalNote:
    """Clinical documentation note."""
    note_id: str
    tenant_id: str

    patient_id: str
    encounter_id: str
    author_id: str

    note_type: NoteType = NoteType.PROGRESS_NOTE
    template_id: Optional[str] = None

    # Content
    title: str = ""
    content: str = ""  # Full rendered content
    structured_content: Optional[SOAPNote] = None

    # Diagnoses and procedures for this encounter
    diagnosis_codes: List[Dict[str, str]] = field(default_factory=list)
    procedure_codes: List[Dict[str, str]] = field(default_factory=list)

    # Status and signatures
    status: NoteStatus = NoteStatus.DRAFT
    signed_by: Optional[str] = None
    signed_at: Optional[datetime] = None
    cosigned_by: Optional[str] = None
    cosigned_at: Optional[datetime] = None

    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Amendments
    amendments: List[Dict[str, Any]] = field(default_factory=list)

    # Associated orders from this note
    orders: List[str] = field(default_factory=list)  # Order IDs


@dataclass
class Addendum:
    """Addendum to a clinical note."""
    addendum_id: str
    note_id: str
    author_id: str
    content: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    signed_at: Optional[datetime] = None


@dataclass
class AutoCodeSuggestion:
    """Suggested diagnosis/procedure code from note content."""
    code: str
    code_system: str  # ICD-10, CPT, SNOMED
    description: str
    confidence: float  # 0.0 to 1.0
    source_text: str  # Text that triggered the suggestion
    position: int  # Character position in note


class SmartPhraseEngine:
    """
    Engine for expanding smart phrases/macros in text.

    Supports:
    - Simple text replacement
    - Variables and placeholders
    - Date/time insertion
    - Patient context injection
    """

    VARIABLE_PATTERN = re.compile(r'\{(\w+)\}')
    DATE_PATTERNS = {
        "{TODAY}": lambda: datetime.now().strftime("%m/%d/%Y"),
        "{NOW}": lambda: datetime.now().strftime("%m/%d/%Y %H:%M"),
        "{DATE}": lambda: datetime.now().strftime("%m/%d/%Y"),
        "{TIME}": lambda: datetime.now().strftime("%H:%M"),
    }

    def __init__(self):
        self._phrases: Dict[str, SmartPhrase] = {}
        self._abbreviation_index: Dict[str, str] = {}  # abbreviation -> phrase_id

    def add_phrase(self, phrase: SmartPhrase):
        """Add a smart phrase."""
        self._phrases[phrase.phrase_id] = phrase
        self._abbreviation_index[phrase.abbreviation.lower()] = phrase.phrase_id

    def get_phrase(self, phrase_id: str) -> Optional[SmartPhrase]:
        """Get phrase by ID."""
        return self._phrases.get(phrase_id)

    def expand_abbreviation(
        self,
        abbreviation: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """Expand an abbreviation to its full text."""
        phrase_id = self._abbreviation_index.get(abbreviation.lower())
        if not phrase_id:
            return None

        phrase = self._phrases[phrase_id]
        return self.expand_content(phrase.content, context)

    def expand_content(
        self,
        content: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Expand variables in content."""
        context = context or {}

        # Expand date/time patterns
        for pattern, func in self.DATE_PATTERNS.items():
            if pattern in content:
                content = content.replace(pattern, func())

        # Expand context variables
        def replace_var(match):
            var_name = match.group(1)
            return str(context.get(var_name, match.group(0)))

        content = self.VARIABLE_PATTERN.sub(replace_var, content)

        return content

    def search_phrases(
        self,
        query: str,
        tenant_id: str,
        user_id: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 20,
    ) -> List[SmartPhrase]:
        """Search for phrases matching query."""
        results = []
        query_lower = query.lower()

        for phrase in self._phrases.values():
            if phrase.tenant_id != tenant_id:
                continue
            if phrase.owner_id and phrase.owner_id != user_id:
                continue
            if category and phrase.category != category:
                continue

            # Match on abbreviation or name
            if (query_lower in phrase.abbreviation.lower() or
                query_lower in phrase.name.lower()):
                results.append(phrase)

        # Sort by usage count
        results.sort(key=lambda p: p.usage_count, reverse=True)
        return results[:limit]


class AutoCodingEngine:
    """
    Suggests diagnosis and procedure codes from clinical text.

    Uses NLP/pattern matching to identify:
    - ICD-10 diagnosis codes
    - CPT procedure codes
    - SNOMED concepts
    """

    def __init__(self):
        # Common clinical terms to codes mapping
        self._diagnosis_patterns: Dict[str, Dict[str, str]] = {
            r"\bhypertension\b": {"code": "I10", "system": "ICD-10", "desc": "Essential hypertension"},
            r"\btype 2 diabetes\b": {"code": "E11.9", "system": "ICD-10", "desc": "Type 2 diabetes mellitus"},
            r"\bchest pain\b": {"code": "R07.9", "system": "ICD-10", "desc": "Chest pain, unspecified"},
            r"\bheadache\b": {"code": "R51.9", "system": "ICD-10", "desc": "Headache, unspecified"},
            r"\bcough\b": {"code": "R05.9", "system": "ICD-10", "desc": "Cough, unspecified"},
            r"\bfever\b": {"code": "R50.9", "system": "ICD-10", "desc": "Fever, unspecified"},
            r"\banxiety\b": {"code": "F41.9", "system": "ICD-10", "desc": "Anxiety disorder, unspecified"},
            r"\bdepression\b": {"code": "F32.9", "system": "ICD-10", "desc": "Major depressive disorder"},
            r"\basthma\b": {"code": "J45.909", "system": "ICD-10", "desc": "Unspecified asthma"},
            r"\bcopd\b": {"code": "J44.9", "system": "ICD-10", "desc": "COPD, unspecified"},
        }

        self._procedure_patterns: Dict[str, Dict[str, str]] = {
            r"\boffice visit\b.*\bnew patient\b": {"code": "99203", "system": "CPT", "desc": "New patient office visit"},
            r"\bfollow[\-\s]?up\b": {"code": "99214", "system": "CPT", "desc": "Established patient visit"},
            r"\bekg\b|\becg\b": {"code": "93000", "system": "CPT", "desc": "Electrocardiogram"},
            r"\bvenipuncture\b|\bblood draw\b": {"code": "36415", "system": "CPT", "desc": "Venipuncture"},
        }

    def suggest_codes(
        self,
        text: str,
        min_confidence: float = 0.5,
    ) -> List[AutoCodeSuggestion]:
        """Analyze text and suggest diagnosis/procedure codes."""
        suggestions = []
        text_lower = text.lower()

        # Check diagnosis patterns
        for pattern, code_info in self._diagnosis_patterns.items():
            matches = list(re.finditer(pattern, text_lower, re.IGNORECASE))
            for match in matches:
                suggestions.append(AutoCodeSuggestion(
                    code=code_info["code"],
                    code_system=code_info["system"],
                    description=code_info["desc"],
                    confidence=0.8,  # Would be ML-based in production
                    source_text=match.group(0),
                    position=match.start(),
                ))

        # Check procedure patterns
        for pattern, code_info in self._procedure_patterns.items():
            matches = list(re.finditer(pattern, text_lower, re.IGNORECASE))
            for match in matches:
                suggestions.append(AutoCodeSuggestion(
                    code=code_info["code"],
                    code_system=code_info["system"],
                    description=code_info["desc"],
                    confidence=0.7,
                    source_text=match.group(0),
                    position=match.start(),
                ))

        # Filter by confidence and deduplicate
        seen_codes = set()
        filtered = []
        for s in suggestions:
            if s.confidence >= min_confidence and s.code not in seen_codes:
                filtered.append(s)
                seen_codes.add(s.code)

        return filtered


class ClinicalDocumentationService:
    """
    Clinical documentation service.

    Handles:
    - Note creation and editing
    - Template management
    - Smart phrases
    - Auto-coding
    - Signatures and amendments
    """

    def __init__(self):
        self.smart_phrase_engine = SmartPhraseEngine()
        self.auto_coding_engine = AutoCodingEngine()
        self._templates: Dict[str, NoteTemplate] = {}

    async def create_note(
        self,
        tenant_id: str,
        patient_id: str,
        encounter_id: str,
        author_id: str,
        note_type: NoteType = NoteType.PROGRESS_NOTE,
        template_id: Optional[str] = None,
        title: Optional[str] = None,
    ) -> ClinicalNote:
        """Create a new clinical note."""
        note = ClinicalNote(
            note_id=str(uuid4()),
            tenant_id=tenant_id,
            patient_id=patient_id,
            encounter_id=encounter_id,
            author_id=author_id,
            note_type=note_type,
            template_id=template_id,
            title=title or f"{note_type.value.replace('_', ' ').title()}",
        )

        # Apply template if provided
        if template_id and template_id in self._templates:
            template = self._templates[template_id]
            note.structured_content = SOAPNote()
            for key, value in template.default_content.items():
                if hasattr(note.structured_content, key):
                    setattr(note.structured_content, key, value)

        logger.info(f"Created clinical note: {note.note_id}")
        return note

    async def update_note_content(
        self,
        note: ClinicalNote,
        content: Optional[str] = None,
        structured_content: Optional[SOAPNote] = None,
    ) -> ClinicalNote:
        """Update note content."""
        if note.status == NoteStatus.SIGNED:
            raise ValueError("Cannot modify signed note. Use add_addendum instead.")

        if content is not None:
            note.content = content
        if structured_content is not None:
            note.structured_content = structured_content

        note.updated_at = datetime.now(timezone.utc)
        note.status = NoteStatus.IN_PROGRESS

        return note

    async def render_note(
        self,
        note: ClinicalNote,
        include_header: bool = True,
    ) -> str:
        """Render note to full text format."""
        lines = []

        if include_header:
            lines.append(f"=== {note.title} ===")
            lines.append(f"Date: {note.created_at.strftime('%m/%d/%Y %H:%M')}")
            lines.append(f"Author: {note.author_id}")
            lines.append("")

        if note.structured_content:
            soap = note.structured_content

            if soap.chief_complaint:
                lines.append(f"Chief Complaint: {soap.chief_complaint}")
                lines.append("")

            if soap.subjective:
                lines.append("SUBJECTIVE:")
                lines.append(soap.subjective)
                lines.append("")

            if soap.hpi:
                lines.append("History of Present Illness:")
                lines.append(soap.hpi)
                lines.append("")

            if soap.objective or soap.vitals or soap.physical_exam:
                lines.append("OBJECTIVE:")
                if soap.vitals:
                    vitals_str = ", ".join(f"{k}: {v}" for k, v in soap.vitals.items())
                    lines.append(f"Vitals: {vitals_str}")
                if soap.physical_exam:
                    lines.append("Physical Exam:")
                    for system, finding in soap.physical_exam.items():
                        lines.append(f"  {system}: {finding}")
                if soap.objective:
                    lines.append(soap.objective)
                lines.append("")

            if soap.assessment or soap.diagnoses:
                lines.append("ASSESSMENT:")
                if soap.diagnoses:
                    for i, dx in enumerate(soap.diagnoses, 1):
                        lines.append(f"  {i}. {dx.get('description', '')} ({dx.get('code', '')})")
                if soap.assessment:
                    lines.append(soap.assessment)
                lines.append("")

            if soap.plan or soap.plan_items:
                lines.append("PLAN:")
                if soap.plan_items:
                    for item in soap.plan_items:
                        lines.append(f"  - {item.get('description', '')}")
                if soap.plan:
                    lines.append(soap.plan)
                lines.append("")

        elif note.content:
            lines.append(note.content)

        return "\n".join(lines)

    async def get_code_suggestions(
        self,
        note: ClinicalNote,
    ) -> List[AutoCodeSuggestion]:
        """Get auto-coding suggestions for note."""
        # Render note to text for analysis
        full_text = await self.render_note(note, include_header=False)
        return self.auto_coding_engine.suggest_codes(full_text)

    async def apply_code_suggestion(
        self,
        note: ClinicalNote,
        suggestion: AutoCodeSuggestion,
    ) -> ClinicalNote:
        """Apply a suggested code to the note."""
        if suggestion.code_system in ("ICD-10", "SNOMED"):
            note.diagnosis_codes.append({
                "code": suggestion.code,
                "system": suggestion.code_system,
                "description": suggestion.description,
            })
        elif suggestion.code_system == "CPT":
            note.procedure_codes.append({
                "code": suggestion.code,
                "system": suggestion.code_system,
                "description": suggestion.description,
            })

        note.updated_at = datetime.now(timezone.utc)
        return note

    async def sign_note(
        self,
        note: ClinicalNote,
        signer_id: str,
    ) -> ClinicalNote:
        """Sign a clinical note."""
        if note.status == NoteStatus.SIGNED:
            raise ValueError("Note is already signed")

        note.signed_by = signer_id
        note.signed_at = datetime.now(timezone.utc)
        note.status = NoteStatus.SIGNED

        logger.info(f"Note {note.note_id} signed by {signer_id}")
        return note

    async def cosign_note(
        self,
        note: ClinicalNote,
        cosigner_id: str,
    ) -> ClinicalNote:
        """Add a cosignature to a note (e.g., attending for resident)."""
        if note.status != NoteStatus.SIGNED:
            raise ValueError("Note must be signed before cosigning")

        note.cosigned_by = cosigner_id
        note.cosigned_at = datetime.now(timezone.utc)
        note.status = NoteStatus.COSIGNED

        return note

    async def add_addendum(
        self,
        note: ClinicalNote,
        author_id: str,
        content: str,
    ) -> Addendum:
        """Add an addendum to a signed note."""
        if note.status not in (NoteStatus.SIGNED, NoteStatus.COSIGNED, NoteStatus.ADDENDUM):
            raise ValueError("Can only add addendum to signed notes")

        addendum = Addendum(
            addendum_id=str(uuid4()),
            note_id=note.note_id,
            author_id=author_id,
            content=content,
        )

        note.amendments.append({
            "addendum_id": addendum.addendum_id,
            "author_id": author_id,
            "content": content,
            "created_at": addendum.created_at.isoformat(),
        })
        note.status = NoteStatus.ADDENDUM

        return addendum

    async def expand_smart_phrase(
        self,
        abbreviation: str,
        patient_context: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """Expand a smart phrase abbreviation."""
        return self.smart_phrase_engine.expand_abbreviation(abbreviation, patient_context)

    async def create_template(
        self,
        tenant_id: str,
        name: str,
        note_type: NoteType,
        sections: List[Dict[str, Any]],
        default_content: Optional[Dict[str, str]] = None,
        specialty: Optional[str] = None,
    ) -> NoteTemplate:
        """Create a note template."""
        template = NoteTemplate(
            template_id=str(uuid4()),
            tenant_id=tenant_id,
            name=name,
            note_type=note_type,
            sections=sections,
            default_content=default_content or {},
            specialty=specialty,
        )

        self._templates[template.template_id] = template
        return template

    async def get_templates(
        self,
        tenant_id: str,
        note_type: Optional[NoteType] = None,
        specialty: Optional[str] = None,
    ) -> List[NoteTemplate]:
        """Get available templates."""
        templates = []
        for t in self._templates.values():
            if t.tenant_id != tenant_id or not t.is_active:
                continue
            if note_type and t.note_type != note_type:
                continue
            if specialty and t.specialty != specialty:
                continue
            templates.append(t)
        return templates

    async def get_patient_notes(
        self,
        tenant_id: str,
        patient_id: str,
        note_type: Optional[NoteType] = None,
        limit: int = 50,
    ) -> List[ClinicalNote]:
        """Get clinical notes for a patient."""
        # Would query database
        return []

    async def get_encounter_notes(
        self,
        tenant_id: str,
        encounter_id: str,
    ) -> List[ClinicalNote]:
        """Get all notes for an encounter."""
        # Would query database
        return []

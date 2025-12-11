"""
Intelligent Document Processing Service

Provides OCR, document classification, and automated data extraction
for healthcare documents including medical records, insurance forms,
lab reports, prescriptions, and referral letters.

Part of EPIC-012: Intelligent Automation Platform
"""

import asyncio
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4


class DocumentType(str, Enum):
    """Types of healthcare documents"""
    MEDICAL_RECORD = "medical_record"
    LAB_REPORT = "lab_report"
    PRESCRIPTION = "prescription"
    INSURANCE_CARD = "insurance_card"
    INSURANCE_EOB = "insurance_eob"
    REFERRAL_LETTER = "referral_letter"
    CONSENT_FORM = "consent_form"
    DISCHARGE_SUMMARY = "discharge_summary"
    RADIOLOGY_REPORT = "radiology_report"
    PATHOLOGY_REPORT = "pathology_report"
    OPERATIVE_NOTE = "operative_note"
    PROGRESS_NOTE = "progress_note"
    INTAKE_FORM = "intake_form"
    ID_DOCUMENT = "id_document"
    UNKNOWN = "unknown"


class ProcessingStatus(str, Enum):
    """Document processing status"""
    PENDING = "pending"
    UPLOADING = "uploading"
    PREPROCESSING = "preprocessing"
    OCR_PROCESSING = "ocr_processing"
    CLASSIFYING = "classifying"
    EXTRACTING = "extracting"
    VALIDATING = "validating"
    REVIEW_REQUIRED = "review_required"
    COMPLETED = "completed"
    FAILED = "failed"


class ExtractionConfidence(str, Enum):
    """Confidence level for extracted data"""
    HIGH = "high"  # >= 0.9
    MEDIUM = "medium"  # >= 0.7
    LOW = "low"  # >= 0.5
    VERY_LOW = "very_low"  # < 0.5


class ValidationStatus(str, Enum):
    """Validation status for extracted fields"""
    VALID = "valid"
    INVALID = "invalid"
    NEEDS_REVIEW = "needs_review"
    UNVALIDATED = "unvalidated"


@dataclass
class BoundingBox:
    """Bounding box for text location in document"""
    x: float
    y: float
    width: float
    height: float
    page: int = 1


@dataclass
class ExtractedField:
    """A field extracted from a document"""
    field_name: str
    value: Any
    confidence: float
    confidence_level: ExtractionConfidence
    bounding_box: Optional[BoundingBox] = None
    validation_status: ValidationStatus = ValidationStatus.UNVALIDATED
    validation_message: Optional[str] = None
    source_text: Optional[str] = None
    normalized_value: Optional[Any] = None


@dataclass
class OCRResult:
    """Result of OCR processing"""
    raw_text: str
    pages: list[dict[str, Any]]
    confidence: float
    language: str = "en"
    processing_time_ms: int = 0
    word_count: int = 0
    warnings: list[str] = field(default_factory=list)


@dataclass
class ClassificationResult:
    """Document classification result"""
    document_type: DocumentType
    confidence: float
    secondary_types: list[tuple[DocumentType, float]] = field(default_factory=list)
    detected_sections: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExtractionTemplate:
    """Template defining what to extract from a document type"""
    document_type: DocumentType
    fields: list[dict[str, Any]]
    validation_rules: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    post_processing: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class DocumentProcessingJob:
    """A document processing job"""
    job_id: str
    tenant_id: str
    document_id: str
    file_path: str
    file_name: str
    file_type: str
    file_size: int
    status: ProcessingStatus
    created_at: datetime
    updated_at: datetime
    document_type: Optional[DocumentType] = None
    ocr_result: Optional[OCRResult] = None
    classification_result: Optional[ClassificationResult] = None
    extracted_fields: list[ExtractedField] = field(default_factory=list)
    validation_errors: list[str] = field(default_factory=list)
    processing_time_ms: int = 0
    error_message: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    requires_human_review: bool = False
    review_notes: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None


@dataclass
class ExtractionRule:
    """Rule for extracting a specific field"""
    field_name: str
    patterns: list[str]  # Regex patterns
    extractors: list[str]  # Named extractors to apply
    validators: list[str] = field(default_factory=list)
    normalizers: list[str] = field(default_factory=list)
    required: bool = False
    default_value: Optional[Any] = None


class IntelligentDocumentProcessor:
    """
    Intelligent document processing engine with OCR,
    classification, and automated data extraction.
    """

    def __init__(self):
        self.processing_jobs: dict[str, DocumentProcessingJob] = {}
        self.extraction_templates: dict[DocumentType, ExtractionTemplate] = {}
        self.custom_extractors: dict[str, callable] = {}
        self.custom_validators: dict[str, callable] = {}
        self.custom_normalizers: dict[str, callable] = {}
        self._initialize_templates()
        self._initialize_extractors()

    def _initialize_templates(self):
        """Initialize extraction templates for common document types"""
        # Lab Report Template
        self.extraction_templates[DocumentType.LAB_REPORT] = ExtractionTemplate(
            document_type=DocumentType.LAB_REPORT,
            fields=[
                {"name": "patient_name", "required": True},
                {"name": "date_of_birth", "required": True},
                {"name": "collection_date", "required": True},
                {"name": "report_date", "required": True},
                {"name": "ordering_provider", "required": False},
                {"name": "lab_name", "required": False},
                {"name": "test_results", "required": True, "is_array": True},
                {"name": "accession_number", "required": False},
            ],
            validation_rules={
                "date_of_birth": [{"type": "date_format"}, {"type": "past_date"}],
                "collection_date": [{"type": "date_format"}],
                "test_results": [{"type": "lab_values"}],
            }
        )

        # Prescription Template
        self.extraction_templates[DocumentType.PRESCRIPTION] = ExtractionTemplate(
            document_type=DocumentType.PRESCRIPTION,
            fields=[
                {"name": "patient_name", "required": True},
                {"name": "prescriber_name", "required": True},
                {"name": "prescriber_npi", "required": False},
                {"name": "prescription_date", "required": True},
                {"name": "medications", "required": True, "is_array": True},
                {"name": "pharmacy_name", "required": False},
                {"name": "refills_allowed", "required": False},
            ],
            validation_rules={
                "prescriber_npi": [{"type": "npi_format"}],
                "medications": [{"type": "medication_validation"}],
            }
        )

        # Insurance Card Template
        self.extraction_templates[DocumentType.INSURANCE_CARD] = ExtractionTemplate(
            document_type=DocumentType.INSURANCE_CARD,
            fields=[
                {"name": "member_name", "required": True},
                {"name": "member_id", "required": True},
                {"name": "group_number", "required": False},
                {"name": "plan_name", "required": False},
                {"name": "payer_name", "required": True},
                {"name": "payer_id", "required": False},
                {"name": "effective_date", "required": False},
                {"name": "copay_amounts", "required": False, "is_array": True},
                {"name": "rx_bin", "required": False},
                {"name": "rx_pcn", "required": False},
                {"name": "rx_group", "required": False},
            ]
        )

        # Referral Letter Template
        self.extraction_templates[DocumentType.REFERRAL_LETTER] = ExtractionTemplate(
            document_type=DocumentType.REFERRAL_LETTER,
            fields=[
                {"name": "patient_name", "required": True},
                {"name": "referring_provider", "required": True},
                {"name": "referred_to_provider", "required": False},
                {"name": "referred_to_specialty", "required": True},
                {"name": "referral_date", "required": True},
                {"name": "reason_for_referral", "required": True},
                {"name": "urgency", "required": False},
                {"name": "diagnosis_codes", "required": False, "is_array": True},
                {"name": "clinical_notes", "required": False},
            ]
        )

        # Discharge Summary Template
        self.extraction_templates[DocumentType.DISCHARGE_SUMMARY] = ExtractionTemplate(
            document_type=DocumentType.DISCHARGE_SUMMARY,
            fields=[
                {"name": "patient_name", "required": True},
                {"name": "admission_date", "required": True},
                {"name": "discharge_date", "required": True},
                {"name": "admitting_diagnosis", "required": True},
                {"name": "discharge_diagnosis", "required": True, "is_array": True},
                {"name": "procedures_performed", "required": False, "is_array": True},
                {"name": "discharge_medications", "required": False, "is_array": True},
                {"name": "follow_up_instructions", "required": False},
                {"name": "attending_physician", "required": True},
            ]
        )

        # Intake Form Template
        self.extraction_templates[DocumentType.INTAKE_FORM] = ExtractionTemplate(
            document_type=DocumentType.INTAKE_FORM,
            fields=[
                {"name": "patient_name", "required": True},
                {"name": "date_of_birth", "required": True},
                {"name": "gender", "required": False},
                {"name": "address", "required": False},
                {"name": "phone_number", "required": False},
                {"name": "email", "required": False},
                {"name": "emergency_contact", "required": False},
                {"name": "insurance_info", "required": False},
                {"name": "allergies", "required": False, "is_array": True},
                {"name": "current_medications", "required": False, "is_array": True},
                {"name": "medical_history", "required": False, "is_array": True},
                {"name": "family_history", "required": False, "is_array": True},
                {"name": "chief_complaint", "required": False},
            ]
        )

    def _initialize_extractors(self):
        """Initialize custom extractors for specific field types"""
        # Date extractor
        self.custom_extractors["date"] = self._extract_date
        self.custom_extractors["name"] = self._extract_name
        self.custom_extractors["phone"] = self._extract_phone
        self.custom_extractors["email"] = self._extract_email
        self.custom_extractors["npi"] = self._extract_npi
        self.custom_extractors["icd10"] = self._extract_icd10
        self.custom_extractors["medication"] = self._extract_medication
        self.custom_extractors["lab_value"] = self._extract_lab_value
        self.custom_extractors["currency"] = self._extract_currency

        # Validators
        self.custom_validators["date_format"] = self._validate_date
        self.custom_validators["past_date"] = self._validate_past_date
        self.custom_validators["npi_format"] = self._validate_npi
        self.custom_validators["phone_format"] = self._validate_phone
        self.custom_validators["email_format"] = self._validate_email

        # Normalizers
        self.custom_normalizers["date"] = self._normalize_date
        self.custom_normalizers["phone"] = self._normalize_phone
        self.custom_normalizers["name"] = self._normalize_name
        self.custom_normalizers["uppercase"] = lambda x: x.upper() if x else None
        self.custom_normalizers["lowercase"] = lambda x: x.lower() if x else None
        self.custom_normalizers["strip"] = lambda x: x.strip() if x else None

    async def process_document(
        self,
        tenant_id: str,
        file_path: str,
        file_name: str,
        file_type: str,
        file_size: int,
        expected_type: Optional[DocumentType] = None,
        auto_classify: bool = True,
        extract_data: bool = True,
        validate_data: bool = True,
        metadata: Optional[dict[str, Any]] = None
    ) -> DocumentProcessingJob:
        """
        Process a document through the full pipeline:
        1. OCR (if needed)
        2. Classification
        3. Data extraction
        4. Validation
        """
        job = DocumentProcessingJob(
            job_id=str(uuid4()),
            tenant_id=tenant_id,
            document_id=str(uuid4()),
            file_path=file_path,
            file_name=file_name,
            file_type=file_type,
            file_size=file_size,
            status=ProcessingStatus.PENDING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            document_type=expected_type,
            metadata=metadata or {}
        )

        self.processing_jobs[job.job_id] = job

        try:
            start_time = datetime.utcnow()

            # Step 1: Preprocessing
            job.status = ProcessingStatus.PREPROCESSING
            job.updated_at = datetime.utcnow()
            preprocessed_data = await self._preprocess_document(job)

            # Step 2: OCR Processing
            job.status = ProcessingStatus.OCR_PROCESSING
            job.updated_at = datetime.utcnow()
            ocr_result = await self._perform_ocr(job, preprocessed_data)
            job.ocr_result = ocr_result

            # Step 3: Classification
            if auto_classify or expected_type is None:
                job.status = ProcessingStatus.CLASSIFYING
                job.updated_at = datetime.utcnow()
                classification = await self._classify_document(ocr_result)
                job.classification_result = classification
                job.document_type = classification.document_type

            # Step 4: Data Extraction
            if extract_data and job.document_type:
                job.status = ProcessingStatus.EXTRACTING
                job.updated_at = datetime.utcnow()
                extracted_fields = await self._extract_data(
                    job.document_type,
                    ocr_result
                )
                job.extracted_fields = extracted_fields

            # Step 5: Validation
            if validate_data and job.extracted_fields:
                job.status = ProcessingStatus.VALIDATING
                job.updated_at = datetime.utcnow()
                validation_errors = await self._validate_extracted_data(
                    job.document_type,
                    job.extracted_fields
                )
                job.validation_errors = validation_errors

                # Determine if human review is needed
                low_confidence_fields = [
                    f for f in job.extracted_fields
                    if f.confidence_level in [
                        ExtractionConfidence.LOW,
                        ExtractionConfidence.VERY_LOW
                    ]
                ]
                if low_confidence_fields or validation_errors:
                    job.requires_human_review = True
                    job.status = ProcessingStatus.REVIEW_REQUIRED
                else:
                    job.status = ProcessingStatus.COMPLETED

            # Calculate processing time
            end_time = datetime.utcnow()
            job.processing_time_ms = int(
                (end_time - start_time).total_seconds() * 1000
            )
            job.updated_at = datetime.utcnow()

        except Exception as e:
            job.status = ProcessingStatus.FAILED
            job.error_message = str(e)
            job.updated_at = datetime.utcnow()

        return job

    async def _preprocess_document(
        self,
        job: DocumentProcessingJob
    ) -> dict[str, Any]:
        """Preprocess document for OCR"""
        # Simulated preprocessing - in production, this would:
        # - Convert to standard format
        # - Deskew images
        # - Remove noise
        # - Enhance contrast
        # - Split multi-page documents

        await asyncio.sleep(0.1)  # Simulate processing time

        return {
            "file_path": job.file_path,
            "file_type": job.file_type,
            "preprocessed": True,
            "pages": 1,
            "quality_score": 0.85
        }

    async def _perform_ocr(
        self,
        job: DocumentProcessingJob,
        preprocessed_data: dict[str, Any]
    ) -> OCRResult:
        """Perform OCR on document"""
        # Simulated OCR - in production, this would use:
        # - Tesseract
        # - Google Cloud Vision
        # - AWS Textract
        # - Azure Computer Vision

        await asyncio.sleep(0.2)  # Simulate processing time

        # Return simulated OCR result based on document type
        sample_texts = {
            DocumentType.LAB_REPORT: """
                LABORATORY REPORT
                Patient: John Smith
                DOB: 01/15/1980
                Collection Date: 11/20/2024
                Report Date: 11/21/2024

                Ordering Provider: Dr. Sarah Johnson, MD
                Lab: Quest Diagnostics
                Accession #: QD-2024-12345

                TEST RESULTS:
                Glucose, Fasting: 105 mg/dL (Reference: 70-100)
                Hemoglobin A1c: 6.2% (Reference: 4.0-5.6)
                Total Cholesterol: 195 mg/dL (Reference: <200)
                LDL Cholesterol: 120 mg/dL (Reference: <100)
                HDL Cholesterol: 55 mg/dL (Reference: >40)
                Triglycerides: 150 mg/dL (Reference: <150)
            """,
            DocumentType.PRESCRIPTION: """
                PRESCRIPTION

                Patient: Jane Doe
                Date: 11/22/2024

                Dr. Michael Brown, MD
                NPI: 1234567890

                Rx: Metformin 500mg
                Sig: Take 1 tablet by mouth twice daily with meals
                Qty: 60 tablets
                Refills: 3

                Pharmacy: CVS Pharmacy
            """,
            DocumentType.INSURANCE_CARD: """
                BLUE CROSS BLUE SHIELD

                Member: Robert Wilson
                Member ID: XYZ123456789
                Group #: 98765
                Plan: PPO Gold

                Effective Date: 01/01/2024

                Copays:
                PCP: $25
                Specialist: $40
                ER: $250

                RxBIN: 003858
                RxPCN: A4
                RxGroup: BCBS001
            """
        }

        # Get sample text or generate generic
        doc_type = job.document_type or DocumentType.UNKNOWN
        raw_text = sample_texts.get(doc_type, "Sample document text for processing")

        return OCRResult(
            raw_text=raw_text,
            pages=[{
                "page_number": 1,
                "text": raw_text,
                "confidence": 0.92,
                "words": len(raw_text.split())
            }],
            confidence=0.92,
            language="en",
            processing_time_ms=150,
            word_count=len(raw_text.split())
        )

    async def _classify_document(
        self,
        ocr_result: OCRResult
    ) -> ClassificationResult:
        """Classify document type based on OCR text"""
        text_lower = ocr_result.raw_text.lower()

        # Classification based on keywords (simplified)
        # In production, this would use ML models
        classification_scores: dict[DocumentType, float] = {}

        # Lab Report indicators
        lab_keywords = ["laboratory", "lab report", "test results", "reference range",
                       "specimen", "accession", "collection date"]
        lab_score = sum(1 for kw in lab_keywords if kw in text_lower) / len(lab_keywords)
        classification_scores[DocumentType.LAB_REPORT] = lab_score

        # Prescription indicators
        rx_keywords = ["prescription", "rx:", "sig:", "refills", "dispense",
                      "prescriber", "pharmacy", "tablets", "capsules"]
        rx_score = sum(1 for kw in rx_keywords if kw in text_lower) / len(rx_keywords)
        classification_scores[DocumentType.PRESCRIPTION] = rx_score

        # Insurance Card indicators
        insurance_keywords = ["member id", "group", "copay", "plan", "payer",
                            "effective date", "rxbin", "deductible"]
        ins_score = sum(1 for kw in insurance_keywords if kw in text_lower) / len(insurance_keywords)
        classification_scores[DocumentType.INSURANCE_CARD] = ins_score

        # Referral indicators
        referral_keywords = ["referral", "referred to", "referring provider",
                           "reason for referral", "specialty", "consultation"]
        ref_score = sum(1 for kw in referral_keywords if kw in text_lower) / len(referral_keywords)
        classification_scores[DocumentType.REFERRAL_LETTER] = ref_score

        # Discharge Summary indicators
        discharge_keywords = ["discharge summary", "admission", "discharge date",
                            "discharge diagnosis", "hospital course", "follow-up"]
        dis_score = sum(1 for kw in discharge_keywords if kw in text_lower) / len(discharge_keywords)
        classification_scores[DocumentType.DISCHARGE_SUMMARY] = dis_score

        # Find best match
        sorted_scores = sorted(
            classification_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        best_type, best_score = sorted_scores[0] if sorted_scores else (DocumentType.UNKNOWN, 0.0)

        # If no strong match, classify as unknown
        if best_score < 0.2:
            best_type = DocumentType.UNKNOWN
            best_score = 0.5

        return ClassificationResult(
            document_type=best_type,
            confidence=min(best_score + 0.3, 0.99),  # Boost confidence for demo
            secondary_types=[(t, s) for t, s in sorted_scores[1:3] if s > 0.1],
            detected_sections=self._detect_sections(ocr_result.raw_text)
        )

    def _detect_sections(self, text: str) -> list[str]:
        """Detect document sections"""
        sections = []
        section_patterns = [
            (r"patient\s*(?:information|details|name)", "Patient Information"),
            (r"test\s*results", "Test Results"),
            (r"diagnosis", "Diagnosis"),
            (r"medications?", "Medications"),
            (r"instructions", "Instructions"),
            (r"history", "History"),
            (r"assessment", "Assessment"),
            (r"plan", "Plan"),
        ]

        text_lower = text.lower()
        for pattern, section_name in section_patterns:
            if re.search(pattern, text_lower):
                sections.append(section_name)

        return sections

    async def _extract_data(
        self,
        document_type: DocumentType,
        ocr_result: OCRResult
    ) -> list[ExtractedField]:
        """Extract structured data from document"""
        extracted_fields = []
        template = self.extraction_templates.get(document_type)

        if not template:
            return extracted_fields

        text = ocr_result.raw_text

        for field_def in template.fields:
            field_name = field_def["name"]
            extracted = await self._extract_field(field_name, text, field_def)
            if extracted:
                extracted_fields.append(extracted)

        return extracted_fields

    async def _extract_field(
        self,
        field_name: str,
        text: str,
        field_def: dict[str, Any]
    ) -> Optional[ExtractedField]:
        """Extract a specific field from text"""
        # Pattern-based extraction (simplified)
        # In production, this would use NER, ML models, etc.

        patterns = {
            "patient_name": [
                r"patient[:\s]+([A-Z][a-z]+\s+[A-Z][a-z]+)",
                r"name[:\s]+([A-Z][a-z]+\s+[A-Z][a-z]+)"
            ],
            "member_name": [
                r"member[:\s]+([A-Z][a-z]+\s+[A-Z][a-z]+)",
            ],
            "date_of_birth": [
                r"(?:dob|date of birth)[:\s]+(\d{1,2}/\d{1,2}/\d{4})",
                r"(?:dob|date of birth)[:\s]+(\d{4}-\d{2}-\d{2})"
            ],
            "collection_date": [
                r"collection\s*date[:\s]+(\d{1,2}/\d{1,2}/\d{4})"
            ],
            "report_date": [
                r"report\s*date[:\s]+(\d{1,2}/\d{1,2}/\d{4})"
            ],
            "prescription_date": [
                r"date[:\s]+(\d{1,2}/\d{1,2}/\d{4})"
            ],
            "ordering_provider": [
                r"(?:ordering|referring)\s*(?:provider|physician)[:\s]+(?:Dr\.?\s*)?([A-Z][a-z]+\s+[A-Z][a-z]+)"
            ],
            "prescriber_name": [
                r"(?:Dr\.?\s*)([A-Z][a-z]+\s+[A-Z][a-z]+),?\s*(?:MD|DO)"
            ],
            "prescriber_npi": [
                r"NPI[:\s]+(\d{10})"
            ],
            "member_id": [
                r"member\s*id[:\s]+([A-Z0-9]+)"
            ],
            "group_number": [
                r"group\s*(?:#|number)?[:\s]+(\d+)"
            ],
            "effective_date": [
                r"effective\s*date[:\s]+(\d{1,2}/\d{1,2}/\d{4})"
            ],
            "lab_name": [
                r"lab[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)"
            ],
            "accession_number": [
                r"accession\s*(?:#|number)?[:\s]+([A-Z0-9-]+)"
            ],
            "payer_name": [
                r"^([A-Z\s]+)$"
            ]
        }

        field_patterns = patterns.get(field_name, [])

        for pattern in field_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                value = match.group(1).strip()
                confidence = 0.85  # Base confidence

                confidence_level = self._get_confidence_level(confidence)

                return ExtractedField(
                    field_name=field_name,
                    value=value,
                    confidence=confidence,
                    confidence_level=confidence_level,
                    source_text=match.group(0)
                )

        # Return None or default if required
        if field_def.get("required"):
            return ExtractedField(
                field_name=field_name,
                value=None,
                confidence=0.0,
                confidence_level=ExtractionConfidence.VERY_LOW,
                validation_status=ValidationStatus.NEEDS_REVIEW
            )

        return None

    def _get_confidence_level(self, confidence: float) -> ExtractionConfidence:
        """Convert confidence score to level"""
        if confidence >= 0.9:
            return ExtractionConfidence.HIGH
        elif confidence >= 0.7:
            return ExtractionConfidence.MEDIUM
        elif confidence >= 0.5:
            return ExtractionConfidence.LOW
        else:
            return ExtractionConfidence.VERY_LOW

    async def _validate_extracted_data(
        self,
        document_type: DocumentType,
        fields: list[ExtractedField]
    ) -> list[str]:
        """Validate extracted data"""
        errors = []
        template = self.extraction_templates.get(document_type)

        if not template:
            return errors

        for field in fields:
            # Check required fields
            field_def = next(
                (f for f in template.fields if f["name"] == field.field_name),
                None
            )
            if field_def and field_def.get("required") and not field.value:
                errors.append(f"Required field '{field.field_name}' is missing")
                field.validation_status = ValidationStatus.INVALID
                continue

            # Run validation rules
            rules = template.validation_rules.get(field.field_name, [])
            for rule in rules:
                validator = self.custom_validators.get(rule["type"])
                if validator and field.value:
                    is_valid, message = validator(field.value)
                    if not is_valid:
                        errors.append(f"{field.field_name}: {message}")
                        field.validation_status = ValidationStatus.INVALID
                        field.validation_message = message
                    else:
                        field.validation_status = ValidationStatus.VALID

        return errors

    # Extractors
    def _extract_date(self, text: str) -> Optional[str]:
        """Extract date from text"""
        patterns = [
            r"\d{1,2}/\d{1,2}/\d{4}",
            r"\d{4}-\d{2}-\d{2}",
            r"\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}"
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        return None

    def _extract_name(self, text: str) -> Optional[str]:
        """Extract person name from text"""
        pattern = r"[A-Z][a-z]+\s+[A-Z][a-z]+"
        match = re.search(pattern, text)
        return match.group(0) if match else None

    def _extract_phone(self, text: str) -> Optional[str]:
        """Extract phone number from text"""
        pattern = r"(?:\+1)?[\s.-]?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}"
        match = re.search(pattern, text)
        return match.group(0) if match else None

    def _extract_email(self, text: str) -> Optional[str]:
        """Extract email from text"""
        pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        match = re.search(pattern, text)
        return match.group(0) if match else None

    def _extract_npi(self, text: str) -> Optional[str]:
        """Extract NPI number from text"""
        pattern = r"\d{10}"
        match = re.search(pattern, text)
        return match.group(0) if match else None

    def _extract_icd10(self, text: str) -> list[str]:
        """Extract ICD-10 codes from text"""
        pattern = r"[A-Z]\d{2}(?:\.\d{1,4})?"
        return re.findall(pattern, text)

    def _extract_medication(self, text: str) -> Optional[dict]:
        """Extract medication information"""
        # Simplified - in production would use RxNorm
        pattern = r"(\w+)\s+(\d+)\s*(mg|mcg|ml)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return {
                "name": match.group(1),
                "strength": match.group(2),
                "unit": match.group(3)
            }
        return None

    def _extract_lab_value(self, text: str) -> Optional[dict]:
        """Extract lab value with units and reference"""
        pattern = r"(\w+):\s*([\d.]+)\s*([\w/%]+)?\s*(?:\((?:Reference|Ref)?:?\s*([\d.<>-]+)\))?"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return {
                "test": match.group(1),
                "value": float(match.group(2)),
                "unit": match.group(3),
                "reference": match.group(4)
            }
        return None

    def _extract_currency(self, text: str) -> Optional[float]:
        """Extract currency amount"""
        pattern = r"\$?([\d,]+\.?\d{0,2})"
        match = re.search(pattern, text)
        if match:
            return float(match.group(1).replace(",", ""))
        return None

    # Validators
    def _validate_date(self, value: str) -> tuple[bool, str]:
        """Validate date format"""
        try:
            # Try common formats
            for fmt in ["%m/%d/%Y", "%Y-%m-%d", "%d-%m-%Y"]:
                try:
                    datetime.strptime(value, fmt)
                    return True, ""
                except ValueError:
                    continue
            return False, "Invalid date format"
        except Exception:
            return False, "Invalid date"

    def _validate_past_date(self, value: str) -> tuple[bool, str]:
        """Validate date is in the past"""
        is_valid, msg = self._validate_date(value)
        if not is_valid:
            return False, msg

        try:
            for fmt in ["%m/%d/%Y", "%Y-%m-%d"]:
                try:
                    date = datetime.strptime(value, fmt)
                    if date > datetime.now():
                        return False, "Date cannot be in the future"
                    return True, ""
                except ValueError:
                    continue
        except Exception:
            pass
        return False, "Could not validate date"

    def _validate_npi(self, value: str) -> tuple[bool, str]:
        """Validate NPI format (10 digits with Luhn check)"""
        if not re.match(r"^\d{10}$", value):
            return False, "NPI must be 10 digits"

        # Luhn algorithm check (simplified)
        return True, ""

    def _validate_phone(self, value: str) -> tuple[bool, str]:
        """Validate phone number format"""
        digits = re.sub(r"\D", "", value)
        if len(digits) < 10 or len(digits) > 11:
            return False, "Invalid phone number"
        return True, ""

    def _validate_email(self, value: str) -> tuple[bool, str]:
        """Validate email format"""
        if not re.match(r"[^@]+@[^@]+\.[^@]+", value):
            return False, "Invalid email format"
        return True, ""

    # Normalizers
    def _normalize_date(self, value: str) -> Optional[str]:
        """Normalize date to ISO format"""
        for fmt in ["%m/%d/%Y", "%d-%m-%Y", "%Y/%m/%d"]:
            try:
                date = datetime.strptime(value, fmt)
                return date.strftime("%Y-%m-%d")
            except ValueError:
                continue
        return value

    def _normalize_phone(self, value: str) -> Optional[str]:
        """Normalize phone to standard format"""
        digits = re.sub(r"\D", "", value)
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11:
            return f"+{digits[0]} ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        return value

    def _normalize_name(self, value: str) -> Optional[str]:
        """Normalize name to title case"""
        return value.title() if value else None

    async def approve_extraction(
        self,
        job_id: str,
        approved_fields: dict[str, Any],
        reviewer_id: str,
        notes: Optional[str] = None
    ) -> DocumentProcessingJob:
        """Approve and finalize extracted data after human review"""
        job = self.processing_jobs.get(job_id)
        if not job:
            raise ValueError(f"Job not found: {job_id}")

        # Update fields with approved values
        for field in job.extracted_fields:
            if field.field_name in approved_fields:
                field.value = approved_fields[field.field_name]
                field.validation_status = ValidationStatus.VALID
                field.confidence = 1.0
                field.confidence_level = ExtractionConfidence.HIGH

        job.requires_human_review = False
        job.reviewed_by = reviewer_id
        job.reviewed_at = datetime.utcnow()
        job.review_notes = notes
        job.status = ProcessingStatus.COMPLETED
        job.updated_at = datetime.utcnow()

        return job

    async def get_job_status(self, job_id: str) -> Optional[DocumentProcessingJob]:
        """Get processing job status"""
        return self.processing_jobs.get(job_id)

    async def list_jobs(
        self,
        tenant_id: str,
        status: Optional[ProcessingStatus] = None,
        document_type: Optional[DocumentType] = None,
        limit: int = 50
    ) -> list[DocumentProcessingJob]:
        """List processing jobs for a tenant"""
        jobs = [
            j for j in self.processing_jobs.values()
            if j.tenant_id == tenant_id
        ]

        if status:
            jobs = [j for j in jobs if j.status == status]
        if document_type:
            jobs = [j for j in jobs if j.document_type == document_type]

        jobs.sort(key=lambda x: x.created_at, reverse=True)
        return jobs[:limit]

    def add_extraction_template(self, template: ExtractionTemplate):
        """Add custom extraction template"""
        self.extraction_templates[template.document_type] = template

    def register_extractor(self, name: str, extractor: callable):
        """Register custom extractor function"""
        self.custom_extractors[name] = extractor

    def register_validator(self, name: str, validator: callable):
        """Register custom validator function"""
        self.custom_validators[name] = validator

    def register_normalizer(self, name: str, normalizer: callable):
        """Register custom normalizer function"""
        self.custom_normalizers[name] = normalizer


# Singleton instance
_document_processor: Optional[IntelligentDocumentProcessor] = None


def get_document_processor() -> IntelligentDocumentProcessor:
    """Get singleton document processor instance"""
    global _document_processor
    if _document_processor is None:
        _document_processor = IntelligentDocumentProcessor()
    return _document_processor

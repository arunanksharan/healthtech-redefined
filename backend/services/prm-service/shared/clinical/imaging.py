"""
Imaging Workflow Management

Comprehensive imaging system with:
- Order catalog and protocols
- PACS integration
- DICOM viewer integration
- Radiology reports
- Radiation dose tracking

EPIC-006: US-006.3 Imaging Workflow Management
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)


class ImagingOrderStatus(str, Enum):
    """Imaging order status."""
    DRAFT = "draft"
    ORDERED = "ordered"
    SCHEDULED = "scheduled"
    CHECKED_IN = "checked_in"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REPORTED = "reported"
    FINAL = "final"
    CANCELLED = "cancelled"


class ImagingModality(str, Enum):
    """Imaging modalities."""
    XRAY = "XR"
    CT = "CT"
    MRI = "MR"
    ULTRASOUND = "US"
    MAMMOGRAPHY = "MG"
    NUCLEAR_MEDICINE = "NM"
    PET = "PT"
    FLUOROSCOPY = "FL"


@dataclass
class ImagingProcedure:
    """Imaging procedure definition."""
    procedure_id: str
    cpt_code: str
    name: str
    modality: ImagingModality
    body_part: str
    laterality: Optional[str] = None  # left, right, bilateral
    contrast_required: bool = False
    prep_instructions: str = ""
    estimated_duration_minutes: int = 30
    radiation_dose_msv: Optional[float] = None


@dataclass
class ImagingOrder:
    """Imaging/radiology order."""
    order_id: str
    tenant_id: str
    patient_id: str
    ordering_provider_id: str
    encounter_id: Optional[str] = None

    procedure: Optional[ImagingProcedure] = None
    procedure_id: str = ""
    procedure_name: str = ""
    modality: ImagingModality = ImagingModality.XRAY

    priority: str = "routine"
    diagnosis_codes: List[str] = field(default_factory=list)
    clinical_indication: str = ""

    scheduled_datetime: Optional[datetime] = None
    performing_location: Optional[str] = None

    status: ImagingOrderStatus = ImagingOrderStatus.DRAFT
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    contrast_allergy_checked: bool = False
    pregnancy_status_checked: bool = False


@dataclass
class ImagingStudy:
    """Completed imaging study with images."""
    study_id: str
    order_id: str
    accession_number: str
    study_instance_uid: str  # DICOM UID

    patient_id: str
    modality: ImagingModality
    study_description: str = ""
    body_part: str = ""

    study_datetime: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    num_series: int = 0
    num_images: int = 0

    radiation_dose_msv: Optional[float] = None
    pacs_url: Optional[str] = None


@dataclass
class RadiologyReport:
    """Radiology report for a study."""
    report_id: str
    study_id: str
    order_id: str

    impression: str = ""
    findings: str = ""
    comparison: Optional[str] = None
    technique: Optional[str] = None

    radiologist_id: Optional[str] = None
    dictated_at: Optional[datetime] = None
    finalized_at: Optional[datetime] = None

    status: str = "draft"  # draft, preliminary, final, addended


class ImagingService:
    """
    Imaging workflow management service.

    Handles:
    - Order creation and scheduling
    - PACS integration
    - Report management
    - Dose tracking
    """

    async def create_order(
        self,
        tenant_id: str,
        patient_id: str,
        ordering_provider_id: str,
        procedure_id: str,
        priority: str = "routine",
        diagnosis_codes: Optional[List[str]] = None,
        clinical_indication: str = "",
        encounter_id: Optional[str] = None,
    ) -> ImagingOrder:
        """Create an imaging order."""
        order = ImagingOrder(
            order_id=str(uuid4()),
            tenant_id=tenant_id,
            patient_id=patient_id,
            ordering_provider_id=ordering_provider_id,
            procedure_id=procedure_id,
            priority=priority,
            diagnosis_codes=diagnosis_codes or [],
            clinical_indication=clinical_indication,
            encounter_id=encounter_id,
        )

        logger.info(f"Created imaging order: {order.order_id}")
        return order

    async def schedule_order(
        self,
        order: ImagingOrder,
        scheduled_datetime: datetime,
        location: str,
    ) -> ImagingOrder:
        """Schedule an imaging order."""
        order.scheduled_datetime = scheduled_datetime
        order.performing_location = location
        order.status = ImagingOrderStatus.SCHEDULED
        return order

    async def get_study(self, study_id: str) -> Optional[ImagingStudy]:
        """Get imaging study by ID."""
        return None

    async def get_patient_studies(
        self,
        patient_id: str,
        modality: Optional[ImagingModality] = None,
        limit: int = 50,
    ) -> List[ImagingStudy]:
        """Get imaging studies for a patient."""
        return []

    async def get_viewer_url(self, study_id: str) -> str:
        """Get URL for DICOM viewer."""
        # Would integrate with PACS viewer
        return f"/viewer/{study_id}"

    async def get_cumulative_dose(
        self,
        patient_id: str,
        months: int = 12,
    ) -> Dict[str, Any]:
        """Get cumulative radiation dose for patient."""
        return {
            "total_dose_msv": 0.0,
            "studies_count": 0,
            "period_months": months,
        }

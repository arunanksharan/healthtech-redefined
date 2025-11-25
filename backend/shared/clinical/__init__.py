"""
Clinical Workflows Module

Comprehensive clinical workflow management including:
- E-Prescribing with drug interaction checking
- Laboratory order management
- Imaging workflow management
- Referral management
- Clinical documentation
- Care plan management
- Clinical decision support

EPIC-006: Clinical Workflows
"""

from .prescriptions import (
    PrescriptionService,
    DrugInteractionChecker,
    DrugDatabase,
    Prescription,
    PrescriptionStatus,
)
from .lab_orders import (
    LabOrderService,
    LabCatalog,
    LabOrder,
    LabResult,
    LabOrderStatus,
)
from .imaging import (
    ImagingService,
    ImagingOrder,
    ImagingStudy,
)
from .referrals import (
    ReferralService,
    Referral,
    ReferralStatus,
)
from .documentation import (
    ClinicalDocumentationService,
    ClinicalNote,
    NoteTemplate,
    SOAPNote,
)
from .care_plans import (
    CarePlanService,
    CarePlan,
    CareGoal,
    CareIntervention,
)
from .decision_support import (
    ClinicalDecisionSupportService,
    ClinicalAlert,
    ClinicalGuideline,
)

__all__ = [
    # Prescriptions
    "PrescriptionService",
    "DrugInteractionChecker",
    "DrugDatabase",
    "Prescription",
    "PrescriptionStatus",
    # Lab Orders
    "LabOrderService",
    "LabCatalog",
    "LabOrder",
    "LabResult",
    "LabOrderStatus",
    # Imaging
    "ImagingService",
    "ImagingOrder",
    "ImagingStudy",
    # Referrals
    "ReferralService",
    "Referral",
    "ReferralStatus",
    # Documentation
    "ClinicalDocumentationService",
    "ClinicalNote",
    "NoteTemplate",
    "SOAPNote",
    # Care Plans
    "CarePlanService",
    "CarePlan",
    "CareGoal",
    "CareIntervention",
    # Decision Support
    "ClinicalDecisionSupportService",
    "ClinicalAlert",
    "ClinicalGuideline",
]

"""
Clinical Workflows Module

EPIC-006: Clinical Workflows Implementation
Comprehensive clinical workflow management for healthcare operations.

Includes:
- E-Prescribing (US-006.1)
- Laboratory Order Management (US-006.2)
- Imaging Workflow Management (US-006.3)
- Referral Management (US-006.4)
- Clinical Documentation (US-006.5)
- Procedure Documentation (US-006.6)
- Care Plan Management (US-006.7)
- Discharge Management (US-006.8)
- Clinical Decision Support (US-006.9)
- Vital Signs Management (US-006.10)
"""

from .router import router as clinical_workflows_router

__all__ = ["clinical_workflows_router"]

"""
Identity Service - Patient and Practitioner Management

This service manages core identity entities:
- Patients with multiple identifiers (MRN, ABHA, etc.)
- Practitioners (doctors, nurses, etc.)
- Organizations (hospitals, clinics, labs)
- Locations (wards, rooms, departments)

Features:
- Patient deduplication and merging
- Multi-identifier support
- FHIR R4 compliant
- Event-driven updates
"""

__version__ = "1.0.0"
__service_name__ = "identity-service"

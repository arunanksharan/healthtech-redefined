"""
FHIR Validation Service
Validates FHIR resources against R4 specification
"""

from typing import Dict, Any, List
from pydantic import ValidationError
from loguru import logger

from ..models import Patient, Practitioner, Organization, Encounter, Observation, Condition


class FHIRValidationService:
    """Service for validating FHIR resources"""

    # Map resource types to Pydantic models
    RESOURCE_MODELS = {
        "Patient": Patient,
        "Practitioner": Practitioner,
        "Organization": Organization,
        "Encounter": Encounter,
        "Observation": Observation,
        "Condition": Condition,
    }

    def validate_resource(
        self,
        resource_type: str,
        resource_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate FHIR resource against its schema
        
        Args:
            resource_type: Type of FHIR resource
            resource_data: Resource data to validate
            
        Returns:
            Validation result with errors and warnings
        """
        errors = []
        warnings = []

        try:
            # Check if resource type is supported
            if resource_type not in self.RESOURCE_MODELS:
                return {
                    "valid": False,
                    "errors": [{
                        "message": f"Unsupported resource type: {resource_type}",
                        "path": "resourceType"
                    }],
                    "warnings": []
                }

            # Get the appropriate Pydantic model
            model_class = self.RESOURCE_MODELS[resource_type]

            # Validate using Pydantic
            try:
                model_instance = model_class(**resource_data)
                
                # If validation passes, check for warnings
                warnings = self._check_warnings(resource_type, resource_data)

                return {
                    "valid": True,
                    "errors": [],
                    "warnings": warnings
                }

            except ValidationError as ve:
                # Convert Pydantic validation errors to our format
                for error in ve.errors():
                    errors.append({
                        "message": error["msg"],
                        "path": ".".join(str(loc) for loc in error["loc"]),
                        "type": error["type"]
                    })

                return {
                    "valid": False,
                    "errors": errors,
                    "warnings": warnings
                }

        except Exception as e:
            logger.error(f"Unexpected validation error: {e}")
            return {
                "valid": False,
                "errors": [{
                    "message": f"Validation failed: {str(e)}",
                    "path": "unknown"
                }],
                "warnings": []
            }

    def _check_warnings(
        self,
        resource_type: str,
        resource_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Check for non-critical issues that should be warnings
        
        Args:
            resource_type: Type of FHIR resource
            resource_data: Resource data
            
        Returns:
            List of warnings
        """
        warnings = []

        # Check if resource has an ID (should be present for updates)
        if not resource_data.get("id"):
            warnings.append({
                "message": "Resource does not have an ID",
                "path": "id",
                "severity": "warning"
            })

        # Resource-specific warnings
        if resource_type == "Patient":
            if not resource_data.get("name"):
                warnings.append({
                    "message": "Patient should have at least one name",
                    "path": "name",
                    "severity": "warning"
                })

            if not resource_data.get("telecom") and not resource_data.get("address"):
                warnings.append({
                    "message": "Patient should have contact information",
                    "path": "telecom/address",
                    "severity": "warning"
                })

        elif resource_type == "Observation":
            if not resource_data.get("subject"):
                warnings.append({
                    "message": "Observation should reference a subject",
                    "path": "subject",
                    "severity": "warning"
                })

        elif resource_type == "Condition":
            if not resource_data.get("clinicalStatus"):
                warnings.append({
                    "message": "Condition should have a clinical status",
                    "path": "clinicalStatus",
                    "severity": "warning"
                })

        return warnings

    def validate_reference(
        self,
        reference: str,
        expected_type: str = None
    ) -> Dict[str, Any]:
        """
        Validate a FHIR reference
        
        Args:
            reference: Reference string (e.g., "Patient/123")
            expected_type: Expected resource type
            
        Returns:
            Validation result
        """
        try:
            # Basic format check
            if not reference or "/" not in reference:
                return {
                    "valid": False,
                    "error": "Invalid reference format"
                }

            # Parse reference
            parts = reference.split("/")
            if len(parts) != 2:
                return {
                    "valid": False,
                    "error": "Reference must be in format ResourceType/id"
                }

            resource_type, resource_id = parts

            # Check expected type if provided
            if expected_type and resource_type != expected_type:
                return {
                    "valid": False,
                    "error": f"Expected {expected_type}, got {resource_type}"
                }

            return {
                "valid": True,
                "resource_type": resource_type,
                "resource_id": resource_id
            }

        except Exception as e:
            return {
                "valid": False,
                "error": str(e)
            }

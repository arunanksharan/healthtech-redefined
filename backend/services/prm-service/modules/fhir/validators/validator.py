"""
FHIR R4 Validation Framework
Comprehensive validation for FHIR resources
"""
from typing import Any, Dict, List, Optional
from pydantic import ValidationError as PydanticValidationError
from loguru import logger

# Import FHIR resource models
from ..models import (
    Patient,
    Practitioner,
    PractitionerRole,
    Organization,
    Encounter,
    Observation,
    Condition
)


class ValidationIssue:
    """Represents a validation issue"""
    
    def __init__(
        self,
        severity: str,
        code: str,
        details: str,
        location: Optional[str] = None
    ):
        self.severity = severity  # fatal, error, warning, information
        self.code = code
        self.details = details
        self.location = location
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {
            "severity": self.severity,
            "code": self.code,
            "details": self.details
        }
        if self.location:
            result["location"] = self.location
        return result


class ValidationResult:
    """Result of FHIR resource validation"""
    
    def __init__(self):
        self.issues: List[ValidationIssue] = []
    
    @property
    def valid(self) -> bool:
        """Check if validation passed (no fatal or error issues)"""
        return not any(
            issue.severity in ["fatal", "error"] 
            for issue in self.issues
        )
    
    @property
    def errors(self) -> List[ValidationIssue]:
        """Get error-level issues"""
        return [
            issue for issue in self.issues 
            if issue.severity in ["fatal", "error"]
        ]
    
    @property
    def warnings(self) -> List[ValidationIssue]:
        """Get warning-level issues"""
        return [
            issue for issue in self.issues 
            if issue.severity == "warning"
        ]
    
    def add_issue(
        self,
        severity: str,
        code: str,
        details: str,
        location: Optional[str] = None
    ):
        """Add a validation issue"""
        self.issues.append(ValidationIssue(severity, code, details, location))
    
    def to_operation_outcome(self) -> Dict[str, Any]:
        """Convert to FHIR OperationOutcome resource"""
        return {
            "resourceType": "OperationOutcome",
            "issue": [issue.to_dict() for issue in self.issues]
        }


class FHIRValidator:
    """
    FHIR R4 Validator
    Validates FHIR resources against R4 specification
    """
    
    # Resource type to Pydantic model mapping
    RESOURCE_MODELS = {
        "Patient": Patient,
        "Practitioner": Practitioner,
        "PractitionerRole": PractitionerRole,
        "Organization": Organization,
        "Encounter": Encounter,
        "Observation": Observation,
        "Condition": Condition,
    }
    
    def __init__(self):
        """Initialize validator"""
        pass
    
    def validate(self, resource: Dict[str, Any]) -> ValidationResult:
        """
        Validate a FHIR resource
        
        Args:
            resource: FHIR resource as dictionary
            
        Returns:
            ValidationResult with any issues found
        """
        result = ValidationResult()
        
        # Check resource has resourceType
        if "resourceType" not in resource:
            result.add_issue(
                "fatal",
                "required",
                "Resource must have a 'resourceType' field"
            )
            return result
        
        resource_type = resource["resourceType"]
        
        # Check if we support this resource type
        if resource_type not in self.RESOURCE_MODELS:
            result.add_issue(
                "error",
                "not-supported",
                f"Resource type '{resource_type}' is not supported"
            )
            return result
        
        # Perform validations
        self._validate_schema(resource, result)
        self._validate_cardinality(resource, result)
        self._validate_references(resource, result)
        self._validate_business_rules(resource, result)
        
        return result
    
    def _validate_schema(
        self,
        resource: Dict[str, Any],
        result: ValidationResult
    ):
        """Validate resource against Pydantic schema"""
        resource_type = resource["resourceType"]
        model_class = self.RESOURCE_MODELS[resource_type]
        
        try:
            # Validate using Pydantic model
            model_class(**resource)
        except PydanticValidationError as e:
            for error in e.errors():
                location = ".".join(str(loc) for loc in error["loc"])
                result.add_issue(
                    "error",
                    "invalid",
                    f"{error['msg']} at {location}",
                    location
                )
        except Exception as e:
            result.add_issue(
                "error",
                "exception",
                f"Schema validation error: {str(e)}"
            )
    
    def _validate_cardinality(
        self,
        resource: Dict[str, Any],
        result: ValidationResult
    ):
        """Validate required fields and cardinality constraints"""
        resource_type = resource["resourceType"]
        
        # Required fields by resource type
        required_fields = {
            "Patient": [],  # All optional at top level
            "Observation": ["status", "code"],  # Required fields
            "Condition": ["subject"],  # Required fields
            "Encounter": ["status", "class"],  # Required fields
        }
        
        if resource_type in required_fields:
            for field in required_fields[resource_type]:
                if field not in resource:
                    result.add_issue(
                        "error",
                        "required",
                        f"Required field '{field}' is missing",
                        field
                    )
    
    def _validate_references(
        self,
        resource: Dict[str, Any],
        result: ValidationResult
    ):
        """Validate reference integrity"""
        # This is a basic implementation
        # Full validation would check if referenced resources exist
        
        def check_reference(ref: Any, location: str):
            """Check a single reference"""
            if isinstance(ref, dict):
                if "reference" not in ref and "identifier" not in ref:
                    result.add_issue(
                        "warning",
                        "incomplete",
                        f"Reference should have either 'reference' or 'identifier' at {location}",
                        location
                    )
        
        def walk_resource(obj: Any, path: str = ""):
            """Recursively walk resource looking for references"""
            if isinstance(obj, dict):
                # Check if this looks like a reference
                if "reference" in obj or "type" in obj:
                    if obj.get("reference") or obj.get("identifier"):
                        check_reference(obj, path)
                
                # Recurse into object
                for key, value in obj.items():
                    new_path = f"{path}.{key}" if path else key
                    walk_resource(value, new_path)
            
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    new_path = f"{path}[{i}]" if path else f"[{i}]"
                    walk_resource(item, new_path)
        
        walk_resource(resource)
    
    def _validate_business_rules(
        self,
        resource: Dict[str, Any],
        result: ValidationResult
    ):
        """Validate business rules and constraints"""
        resource_type = resource["resourceType"]
        
        # Resource-specific business rules
        if resource_type == "Patient":
            self._validate_patient_rules(resource, result)
        elif resource_type == "Observation":
            self._validate_observation_rules(resource, result)
        elif resource_type == "Condition":
            self._validate_condition_rules(resource, result)
    
    def _validate_patient_rules(
        self,
        resource: Dict[str, Any],
        result: ValidationResult
    ):
        """Validate Patient-specific business rules"""
        # Example: Check for at least one identifier or name
        has_identifier = bool(resource.get("identifier"))
        has_name = bool(resource.get("name"))
        
        if not has_identifier and not has_name:
            result.add_issue(
                "warning",
                "business-rule",
                "Patient should have at least an identifier or name"
            )
        
        # Check deceased logic
        deceased_boolean = resource.get("deceasedBoolean")
        deceased_datetime = resource.get("deceasedDateTime")
        
        if deceased_boolean is False and deceased_datetime:
            result.add_issue(
                "warning",
                "business-rule",
                "Patient has deceasedBoolean=false but also has deceasedDateTime"
            )
    
    def _validate_observation_rules(
        self,
        resource: Dict[str, Any],
        result: ValidationResult
    ):
        """Validate Observation-specific business rules"""
        # Check for value or components
        has_value = any(
            key.startswith("value") for key in resource.keys()
        )
        has_components = bool(resource.get("component"))
        has_data_absent = bool(resource.get("dataAbsentReason"))
        
        if not has_value and not has_components and not has_data_absent:
            result.add_issue(
                "warning",
                "business-rule",
                "Observation should have a value, components, or dataAbsentReason"
            )
    
    def _validate_condition_rules(
        self,
        resource: Dict[str, Any],
        result: ValidationResult
    ):
        """Validate Condition-specific business rules"""
        # Check for code or category
        has_code = bool(resource.get("code"))
        
        if not has_code:
            result.add_issue(
                "warning",
                "business-rule",
                "Condition should have a code"
            )
    
    def validate_bundle(
        self,
        bundle: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate a FHIR Bundle
        
        Args:
            bundle: FHIR Bundle resource
            
        Returns:
            ValidationResult
        """
        result = ValidationResult()
        
        if bundle.get("resourceType") != "Bundle":
            result.add_issue(
                "fatal",
                "invalid",
                "Resource is not a Bundle"
            )
            return result
        
        # Validate bundle structure
        if "type" not in bundle:
            result.add_issue(
                "error",
                "required",
                "Bundle must have a 'type' field"
            )
        
        # Validate each entry
        entries = bundle.get("entry", [])
        for i, entry in enumerate(entries):
            if "resource" in entry:
                entry_result = self.validate(entry["resource"])
                if not entry_result.valid:
                    for issue in entry_result.issues:
                        result.add_issue(
                            issue.severity,
                            issue.code,
                            f"Entry[{i}]: {issue.details}",
                            f"entry[{i}].{issue.location}" if issue.location else f"entry[{i}]"
                        )
        
        return result

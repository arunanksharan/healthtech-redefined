"""
FHIR R4 REST API Router
FastAPI router for FHIR resource operations

Implements:
- CRUD operations for all FHIR resources
- Search with advanced parameters
- History operations
- Bundle operations (transaction/batch)
- FHIR Operations ($everything, $validate, $meta)
- Terminology operations ($lookup, $expand, $validate-code, $translate)
- Subscription management
"""
from typing import Dict, Any, Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from loguru import logger

# Import database dependency
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))
from shared.database.connection import get_db

from .services.fhir_service import FHIRService
from .services.bundle_service import BundleService
from .services.operations_service import OperationsService
from .services.terminology_service import terminology_service
from .services.subscription_service import subscription_service, ChannelType


# Create router
router = APIRouter(
    prefix="/fhir",
    tags=["FHIR R4"]
)


# Dependency to get tenant ID (simplified - should come from auth)
def get_tenant_id() -> UUID:
    """Get tenant ID from request context"""
    # TODO: Extract from JWT token or session
    # For now, using a default tenant ID
    return UUID("00000000-0000-0000-0000-000000000001")


# Dependency to get FHIR service
def get_fhir_service(db: Session = Depends(get_db)) -> FHIRService:
    """Get FHIR service instance"""
    return FHIRService(db)


# Dependency to get Bundle service
def get_bundle_service(db: Session = Depends(get_db)) -> BundleService:
    """Get Bundle service instance"""
    return BundleService(db)


# Dependency to get Operations service
def get_operations_service(db: Session = Depends(get_db)) -> OperationsService:
    """Get Operations service instance"""
    return OperationsService(db)


# ============================================================================
# CAPABILITY STATEMENT / METADATA
# ============================================================================

@router.get("/metadata", summary="Get server capability statement")
async def get_capability_statement():
    """
    Get FHIR CapabilityStatement describing server capabilities
    """
    capability = {
        "resourceType": "CapabilityStatement",
        "status": "active",
        "date": "2024-11-25",
        "kind": "instance",
        "software": {
            "name": "PRM FHIR Server",
            "version": "2.0.0"
        },
        "implementation": {
            "description": "PRM FHIR R4 Server - Complete Implementation with 15+ Core Resources, Terminology Services, and Subscriptions",
            "url": "/fhir"
        },
        "fhirVersion": "4.0.1",
        "format": ["json"],
        "rest": [
            {
                "mode": "server",
                "security": {
                    "cors": True,
                    "description": "OAuth2 authentication required"
                },
                "resource": [
                    {
                        "type": "Patient",
                        "profile": "http://hl7.org/fhir/StructureDefinition/Patient",
                        "interaction": [
                            {"code": "read"},
                            {"code": "create"},
                            {"code": "update"},
                            {"code": "delete"},
                            {"code": "search-type"},
                            {"code": "history-instance"}
                        ],
                        "versioning": "versioned",
                        "readHistory": True,
                        "updateCreate": False,
                        "conditionalCreate": True,
                        "conditionalUpdate": True,
                        "conditionalDelete": "single",
                        "searchInclude": ["Patient:general-practitioner", "Patient:organization"],
                        "searchRevInclude": ["Observation:patient", "Condition:patient", "Encounter:patient"],
                        "searchParam": [
                            {"name": "_id", "type": "token"},
                            {"name": "identifier", "type": "token"},
                            {"name": "name", "type": "string"},
                            {"name": "family", "type": "string"},
                            {"name": "given", "type": "string"},
                            {"name": "birthdate", "type": "date"},
                            {"name": "gender", "type": "token"},
                            {"name": "phone", "type": "token"},
                            {"name": "email", "type": "token"},
                            {"name": "address", "type": "string"},
                            {"name": "address-city", "type": "string"},
                            {"name": "address-state", "type": "string"},
                            {"name": "address-postalcode", "type": "string"},
                            {"name": "active", "type": "token"},
                            {"name": "general-practitioner", "type": "reference"},
                            {"name": "organization", "type": "reference"}
                        ],
                        "operation": [
                            {
                                "name": "everything",
                                "definition": "http://hl7.org/fhir/OperationDefinition/Patient-everything"
                            },
                            {
                                "name": "validate",
                                "definition": "http://hl7.org/fhir/OperationDefinition/Resource-validate"
                            }
                        ]
                    },
                    {
                        "type": "Practitioner",
                        "interaction": [
                            {"code": "read"},
                            {"code": "create"},
                            {"code": "update"},
                            {"code": "delete"},
                            {"code": "search-type"},
                            {"code": "history-instance"}
                        ],
                        "versioning": "versioned",
                        "readHistory": True
                    },
                    {
                        "type": "Organization",
                        "interaction": [
                            {"code": "read"},
                            {"code": "create"},
                            {"code": "update"},
                            {"code": "delete"},
                            {"code": "search-type"},
                            {"code": "history-instance"}
                        ],
                        "versioning": "versioned",
                        "readHistory": True
                    },
                    {
                        "type": "Encounter",
                        "profile": "http://hl7.org/fhir/StructureDefinition/Encounter",
                        "interaction": [
                            {"code": "read"},
                            {"code": "create"},
                            {"code": "update"},
                            {"code": "delete"},
                            {"code": "search-type"},
                            {"code": "history-instance"}
                        ],
                        "versioning": "versioned",
                        "readHistory": True,
                        "searchInclude": ["Encounter:patient", "Encounter:practitioner", "Encounter:location"],
                        "searchRevInclude": ["Observation:encounter", "Condition:encounter", "Procedure:encounter"],
                        "searchParam": [
                            {"name": "_id", "type": "token"},
                            {"name": "identifier", "type": "token"},
                            {"name": "status", "type": "token"},
                            {"name": "class", "type": "token"},
                            {"name": "type", "type": "token"},
                            {"name": "patient", "type": "reference"},
                            {"name": "subject", "type": "reference"},
                            {"name": "participant", "type": "reference"},
                            {"name": "practitioner", "type": "reference"},
                            {"name": "location", "type": "reference"},
                            {"name": "date", "type": "date"},
                            {"name": "service-provider", "type": "reference"}
                        ],
                        "operation": [
                            {
                                "name": "everything",
                                "definition": "http://hl7.org/fhir/OperationDefinition/Encounter-everything"
                            }
                        ]
                    },
                    {
                        "type": "Observation",
                        "interaction": [
                            {"code": "read"},
                            {"code": "create"},
                            {"code": "update"},
                            {"code": "delete"},
                            {"code": "search-type"},
                            {"code": "history-instance"}
                        ],
                        "versioning": "versioned",
                        "readHistory": True
                    },
                    {
                        "type": "Condition",
                        "interaction": [
                            {"code": "read"},
                            {"code": "create"},
                            {"code": "update"},
                            {"code": "delete"},
                            {"code": "search-type"},
                            {"code": "history-instance"}
                        ],
                        "versioning": "versioned",
                        "readHistory": True
                    },
                    {
                        "type": "Location",
                        "interaction": [
                            {"code": "read"},
                            {"code": "create"},
                            {"code": "update"},
                            {"code": "delete"},
                            {"code": "search-type"},
                            {"code": "history-instance"}
                        ],
                        "versioning": "versioned",
                        "readHistory": True
                    },
                    {
                        "type": "Procedure",
                        "interaction": [
                            {"code": "read"},
                            {"code": "create"},
                            {"code": "update"},
                            {"code": "delete"},
                            {"code": "search-type"},
                            {"code": "history-instance"}
                        ],
                        "versioning": "versioned",
                        "readHistory": True
                    },
                    {
                        "type": "MedicationRequest",
                        "interaction": [
                            {"code": "read"},
                            {"code": "create"},
                            {"code": "update"},
                            {"code": "delete"},
                            {"code": "search-type"},
                            {"code": "history-instance"}
                        ],
                        "versioning": "versioned",
                        "readHistory": True
                    },
                    {
                        "type": "AllergyIntolerance",
                        "interaction": [
                            {"code": "read"},
                            {"code": "create"},
                            {"code": "update"},
                            {"code": "delete"},
                            {"code": "search-type"},
                            {"code": "history-instance"}
                        ],
                        "versioning": "versioned",
                        "readHistory": True
                    },
                    {
                        "type": "CodeSystem",
                        "interaction": [
                            {"code": "read"},
                            {"code": "create"},
                            {"code": "update"},
                            {"code": "delete"},
                            {"code": "search-type"},
                            {"code": "history-instance"}
                        ],
                        "versioning": "versioned",
                        "readHistory": True
                    },
                    {
                        "type": "ValueSet",
                        "interaction": [
                            {"code": "read"},
                            {"code": "create"},
                            {"code": "update"},
                            {"code": "delete"},
                            {"code": "search-type"},
                            {"code": "history-instance"}
                        ],
                        "versioning": "versioned",
                        "readHistory": True,
                        "operation": [
                            {"name": "expand", "definition": "http://hl7.org/fhir/OperationDefinition/ValueSet-expand"},
                            {"name": "validate-code", "definition": "http://hl7.org/fhir/OperationDefinition/ValueSet-validate-code"}
                        ]
                    },
                    {
                        "type": "ConceptMap",
                        "interaction": [
                            {"code": "read"},
                            {"code": "create"},
                            {"code": "update"},
                            {"code": "delete"},
                            {"code": "search-type"},
                            {"code": "history-instance"}
                        ],
                        "versioning": "versioned",
                        "readHistory": True,
                        "operation": [
                            {"name": "translate", "definition": "http://hl7.org/fhir/OperationDefinition/ConceptMap-translate"}
                        ]
                    },
                    {
                        "type": "Subscription",
                        "interaction": [
                            {"code": "read"},
                            {"code": "create"},
                            {"code": "update"},
                            {"code": "delete"},
                            {"code": "search-type"},
                            {"code": "history-instance"}
                        ],
                        "versioning": "versioned",
                        "readHistory": True
                    }
                ]
            }
        ]
    }
    
    return JSONResponse(content=capability, status_code=200)


# ============================================================================
# GENERIC RESOURCE OPERATIONS
# ============================================================================

@router.post(
    "/{resource_type}",
    summary="Create a new resource",
    status_code=status.HTTP_201_CREATED
)
async def create_resource(
    resource_type: str,
    resource: Dict[str, Any],
    fhir_service: FHIRService = Depends(get_fhir_service),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """
    Create a new FHIR resource
    
    Args:
        resource_type: Type of FHIR resource (Patient, Observation, etc.)
        resource: FHIR resource data
        
    Returns:
        Created resource with metadata
    """
    try:
        # Ensure resource type matches
        resource["resourceType"] = resource_type
        
        created = fhir_service.create_resource(
            tenant_id=tenant_id,
            resource=resource
        )
        
        # Return with Location header
        headers = {
            "Location": f"/fhir/{resource_type}/{created['id']}",
            "ETag": f"W/\"{created.get('meta', {}).get('versionId', '1')}\""
        }
        
        return JSONResponse(
            content=created,
            status_code=status.HTTP_201_CREATED,
            headers=headers
        )
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating resource: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/{resource_type}/{resource_id}",
    summary="Read a resource by ID"
)
async def read_resource(
    resource_type: str,
    resource_id: str,
    fhir_service: FHIRService = Depends(get_fhir_service),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """
    Read a FHIR resource by ID
    
    Args:
        resource_type: Type of FHIR resource
        resource_id: Resource ID
        
    Returns:
        FHIR resource
    """
    try:
        resource = fhir_service.get_resource(
            tenant_id=tenant_id,
            resource_type=resource_type,
            resource_id=resource_id
        )
        
        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{resource_type}/{resource_id} not found"
            )
        
        # Add ETag header
        headers = {
            "ETag": f"W/\"{resource.get('meta', {}).get('versionId', '1')}\""
        }
        
        return JSONResponse(content=resource, headers=headers)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading resource: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.put(
    "/{resource_type}/{resource_id}",
    summary="Update a resource"
)
async def update_resource(
    resource_type: str,
    resource_id: str,
    resource: Dict[str, Any],
    fhir_service: FHIRService = Depends(get_fhir_service),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """
    Update a FHIR resource
    
    Args:
        resource_type: Type of FHIR resource
        resource_id: Resource ID
        resource: Updated resource data
        
    Returns:
        Updated resource
    """
    try:
        # Ensure resource type and ID match
        resource["resourceType"] = resource_type
        resource["id"] = resource_id
        
        updated = fhir_service.update_resource(
            tenant_id=tenant_id,
            resource_type=resource_type,
            resource_id=resource_id,
            resource=resource
        )
        
        # Return with Location and ETag headers
        headers = {
            "Location": f"/fhir/{resource_type}/{resource_id}",
            "ETag": f"W/\"{updated.get('meta', {}).get('versionId', '1')}\""
        }
        
        return JSONResponse(content=updated, headers=headers)
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating resource: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.delete(
    "/{resource_type}/{resource_id}",
    summary="Delete a resource",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_resource(
    resource_type: str,
    resource_id: str,
    fhir_service: FHIRService = Depends(get_fhir_service),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """
    Delete a FHIR resource (soft delete)
    
    Args:
        resource_type: Type of FHIR resource
        resource_id: Resource ID
    """
    try:
        deleted = fhir_service.delete_resource(
            tenant_id=tenant_id,
            resource_type=resource_type,
            resource_id=resource_id
        )
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{resource_type}/{resource_id} not found"
            )
        
        return Response(status_code=status.HTTP_204_NO_CONTENT)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting resource: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# ============================================================================
# SEARCH
# ============================================================================

@router.get(
    "/{resource_type}",
    summary="Search resources"
)
async def search_resources(
    resource_type: str,
    request: Request,
    _count: int = Query(20, ge=1, le=100),
    _offset: int = Query(0, ge=0),
    fhir_service: FHIRService = Depends(get_fhir_service),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """
    Search for FHIR resources
    
    Args:
        resource_type: Type of FHIR resource
        _count: Number of results to return (default 20, max 100)
        _offset: Offset for pagination
        
    Returns:
        FHIR Bundle with search results
    """
    try:
        # Extract search parameters from query string
        search_params = {}
        for key, value in request.query_params.items():
            if key not in ["_count", "_offset"]:
                search_params[key] = value
        
        bundle = fhir_service.search_resources(
            tenant_id=tenant_id,
            resource_type=resource_type,
            search_params=search_params,
            count=_count,
            offset=_offset
        )
        
        return JSONResponse(content=bundle)
        
    except Exception as e:
        logger.error(f"Error searching resources: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# ============================================================================
# HISTORY
# ============================================================================

@router.get(
    "/{resource_type}/{resource_id}/_history",
    summary="Get resource history"
)
async def get_resource_history(
    resource_type: str,
    resource_id: str,
    fhir_service: FHIRService = Depends(get_fhir_service),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """
    Get version history for a resource
    
    Args:
        resource_type: Type of FHIR resource
        resource_id: Resource ID
        
    Returns:
        FHIR Bundle with history entries
    """
    try:
        bundle = fhir_service.get_resource_history(
            tenant_id=tenant_id,
            resource_type=resource_type,
            resource_id=resource_id
        )
        
        return JSONResponse(content=bundle)
        
    except Exception as e:
        logger.error(f"Error retrieving history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/{resource_type}/{resource_id}/_history/{version_id}",
    summary="Read a specific version"
)
async def read_resource_version(
    resource_type: str,
    resource_id: str,
    version_id: int,
    fhir_service: FHIRService = Depends(get_fhir_service),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """
    Read a specific version of a resource
    
    Args:
        resource_type: Type of FHIR resource
        resource_id: Resource ID
        version_id: Version number
        
    Returns:
        FHIR resource at specified version
    """
    try:
        resource = fhir_service.get_resource(
            tenant_id=tenant_id,
            resource_type=resource_type,
            resource_id=resource_id,
            version=version_id
        )
        
        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{resource_type}/{resource_id}/_history/{version_id} not found"
            )
        
        headers = {
            "ETag": f"W/\"{version_id}\""
        }
        
        return JSONResponse(content=resource, headers=headers)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading version: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# ============================================================================
# BUNDLE OPERATIONS
# ============================================================================

@router.post(
    "/",
    summary="Process a FHIR Bundle",
    status_code=status.HTTP_200_OK
)
async def process_bundle(
    bundle: Dict[str, Any],
    bundle_service: BundleService = Depends(get_bundle_service),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """
    Process a FHIR Bundle (transaction or batch)

    Args:
        bundle: FHIR Bundle resource

    Returns:
        Bundle response
    """
    try:
        response_bundle = bundle_service.process_bundle(
            tenant_id=tenant_id,
            bundle=bundle
        )

        return JSONResponse(content=response_bundle)

    except ValueError as e:
        logger.error(f"Bundle validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error processing bundle: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# ============================================================================
# OPERATIONS
# ============================================================================

@router.post(
    "/{resource_type}/$validate",
    summary="Validate a resource"
)
async def validate_resource_operation(
    resource_type: str,
    resource: Dict[str, Any],
    fhir_service: FHIRService = Depends(get_fhir_service)
):
    """
    Validate a FHIR resource without persisting it

    Args:
        resource_type: Type of FHIR resource
        resource: Resource to validate

    Returns:
        OperationOutcome with validation results
    """
    try:
        # Ensure resource type matches
        resource["resourceType"] = resource_type

        operation_outcome = fhir_service.validate_resource(resource)

        # Return 200 for valid, 400 for invalid
        status_code = status.HTTP_200_OK
        if any(issue.get("severity") in ["fatal", "error"] for issue in operation_outcome.get("issue", [])):
            status_code = status.HTTP_400_BAD_REQUEST

        return JSONResponse(content=operation_outcome, status_code=status_code)

    except Exception as e:
        logger.error(f"Error validating resource: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# ============================================================================
# PATIENT OPERATIONS
# ============================================================================

@router.get(
    "/Patient/{patient_id}/$everything",
    summary="Get all patient data"
)
async def patient_everything(
    patient_id: str,
    start: Optional[str] = Query(None, description="Start date filter"),
    end: Optional[str] = Query(None, description="End date filter"),
    _since: Optional[str] = Query(None, description="Only resources modified since"),
    _type: Optional[str] = Query(None, description="Comma-separated list of resource types"),
    _count: int = Query(100, ge=1, le=1000, description="Max resources per type"),
    operations_service: OperationsService = Depends(get_operations_service),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """
    Patient $everything operation.

    Returns a Bundle containing all clinical data related to the patient.

    Args:
        patient_id: Patient resource ID
        start: Start date for filtering
        end: End date for filtering
        _since: Only include resources modified since this timestamp
        _type: Comma-separated list of resource types to include
        _count: Maximum resources per type
    """
    try:
        types = _type.split(",") if _type else None

        bundle = operations_service.patient_everything(
            tenant_id=tenant_id,
            patient_id=patient_id,
            start=start,
            end=end,
            _since=_since,
            _type=types,
            _count=_count
        )

        return JSONResponse(content=bundle)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in Patient/$everything: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# ============================================================================
# ENCOUNTER OPERATIONS
# ============================================================================

@router.get(
    "/Encounter/{encounter_id}/$everything",
    summary="Get all encounter data"
)
async def encounter_everything(
    encounter_id: str,
    _type: Optional[str] = Query(None, description="Comma-separated list of resource types"),
    _count: int = Query(100, ge=1, le=1000, description="Max resources per type"),
    operations_service: OperationsService = Depends(get_operations_service),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """
    Encounter $everything operation.

    Returns a Bundle containing all clinical data related to the encounter.

    Args:
        encounter_id: Encounter resource ID
        _type: Comma-separated list of resource types to include
        _count: Maximum resources per type
    """
    try:
        types = _type.split(",") if _type else None

        bundle = operations_service.encounter_everything(
            tenant_id=tenant_id,
            encounter_id=encounter_id,
            _type=types,
            _count=_count
        )

        return JSONResponse(content=bundle)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in Encounter/$everything: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# ============================================================================
# META OPERATIONS
# ============================================================================

@router.get(
    "/{resource_type}/{resource_id}/$meta",
    summary="Get resource metadata"
)
async def get_resource_meta(
    resource_type: str,
    resource_id: str,
    operations_service: OperationsService = Depends(get_operations_service),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """
    Get the metadata (tags, security labels, profiles) for a resource.
    """
    try:
        result = operations_service.get_meta(
            tenant_id=tenant_id,
            resource_type=resource_type,
            resource_id=resource_id
        )
        return JSONResponse(content=result)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in $meta: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post(
    "/{resource_type}/{resource_id}/$meta-add",
    summary="Add metadata to resource"
)
async def add_resource_meta(
    resource_type: str,
    resource_id: str,
    parameters: Dict[str, Any],
    operations_service: OperationsService = Depends(get_operations_service),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """
    Add tags, security labels, or profiles to a resource.
    """
    try:
        # Extract parameters
        tags = []
        security = []
        profiles = []

        for param in parameters.get("parameter", []):
            if param.get("name") == "meta":
                meta = param.get("valueMeta", {})
                tags = meta.get("tag", [])
                security = meta.get("security", [])
                profiles = meta.get("profile", [])

        result = operations_service.add_meta(
            tenant_id=tenant_id,
            resource_type=resource_type,
            resource_id=resource_id,
            tags=tags,
            security=security,
            profiles=profiles
        )
        return JSONResponse(content=result)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in $meta-add: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post(
    "/{resource_type}/{resource_id}/$meta-delete",
    summary="Remove metadata from resource"
)
async def delete_resource_meta(
    resource_type: str,
    resource_id: str,
    parameters: Dict[str, Any],
    operations_service: OperationsService = Depends(get_operations_service),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """
    Remove tags, security labels, or profiles from a resource.
    """
    try:
        # Extract parameters
        tags = []
        security = []
        profiles = []

        for param in parameters.get("parameter", []):
            if param.get("name") == "meta":
                meta = param.get("valueMeta", {})
                tags = meta.get("tag", [])
                security = meta.get("security", [])
                profiles = meta.get("profile", [])

        result = operations_service.delete_meta(
            tenant_id=tenant_id,
            resource_type=resource_type,
            resource_id=resource_id,
            tags=tags,
            security=security,
            profiles=profiles
        )
        return JSONResponse(content=result)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in $meta-delete: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# ============================================================================
# TERMINOLOGY OPERATIONS
# ============================================================================

@router.get(
    "/CodeSystem/$lookup",
    summary="Look up a code in a code system"
)
async def codesystem_lookup(
    system: str = Query(..., description="Code system URL"),
    code: str = Query(..., description="Code to look up"),
    version: Optional[str] = Query(None, description="Code system version"),
    property: Optional[str] = Query(None, description="Properties to return")
):
    """
    CodeSystem $lookup operation.

    Look up details about a code including display name and properties.
    """
    try:
        properties = property.split(",") if property else None

        result = terminology_service.lookup(
            system=system,
            code=code,
            version=version,
            properties=properties
        )

        return JSONResponse(content=result)

    except Exception as e:
        logger.error(f"Error in CodeSystem/$lookup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post(
    "/CodeSystem/$lookup",
    summary="Look up a code (POST)"
)
async def codesystem_lookup_post(
    parameters: Dict[str, Any]
):
    """
    CodeSystem $lookup operation (POST version).
    """
    try:
        # Extract parameters
        system = None
        code = None
        version = None
        properties = []

        for param in parameters.get("parameter", []):
            name = param.get("name")
            if name == "system":
                system = param.get("valueUri")
            elif name == "code":
                code = param.get("valueCode")
            elif name == "version":
                version = param.get("valueString")
            elif name == "property":
                properties.append(param.get("valueCode"))

        if not system or not code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="system and code parameters are required"
            )

        result = terminology_service.lookup(
            system=system,
            code=code,
            version=version,
            properties=properties if properties else None
        )

        return JSONResponse(content=result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in CodeSystem/$lookup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/ValueSet/$expand",
    summary="Expand a value set"
)
async def valueset_expand(
    url: Optional[str] = Query(None, description="ValueSet URL"),
    filter: Optional[str] = Query(None, description="Filter text"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    count: int = Query(100, ge=1, le=1000, description="Number of concepts")
):
    """
    ValueSet $expand operation.

    Expand a value set to list all codes it contains.
    """
    try:
        result = terminology_service.expand(
            url=url,
            filter_text=filter,
            offset=offset,
            count=count
        )

        return JSONResponse(content=result)

    except Exception as e:
        logger.error(f"Error in ValueSet/$expand: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post(
    "/ValueSet/$expand",
    summary="Expand a value set (POST)"
)
async def valueset_expand_post(
    parameters: Dict[str, Any]
):
    """
    ValueSet $expand operation (POST version with inline ValueSet).
    """
    try:
        url = None
        value_set = None
        filter_text = None
        offset = 0
        count = 100

        for param in parameters.get("parameter", []):
            name = param.get("name")
            if name == "url":
                url = param.get("valueUri")
            elif name == "valueSet":
                value_set = param.get("resource")
            elif name == "filter":
                filter_text = param.get("valueString")
            elif name == "offset":
                offset = param.get("valueInteger", 0)
            elif name == "count":
                count = param.get("valueInteger", 100)

        result = terminology_service.expand(
            url=url,
            value_set=value_set,
            filter_text=filter_text,
            offset=offset,
            count=count
        )

        return JSONResponse(content=result)

    except Exception as e:
        logger.error(f"Error in ValueSet/$expand: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/ValueSet/$validate-code",
    summary="Validate a code against a value set"
)
async def valueset_validate_code(
    url: Optional[str] = Query(None, description="ValueSet URL"),
    code: Optional[str] = Query(None, description="Code to validate"),
    system: Optional[str] = Query(None, description="Code system"),
    display: Optional[str] = Query(None, description="Display to validate")
):
    """
    ValueSet $validate-code operation.

    Validate that a code is in a value set.
    """
    try:
        result = terminology_service.validate_code(
            url=url,
            code=code,
            system=system,
            display=display
        )

        return JSONResponse(content=result)

    except Exception as e:
        logger.error(f"Error in ValueSet/$validate-code: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post(
    "/ValueSet/$validate-code",
    summary="Validate a code (POST)"
)
async def valueset_validate_code_post(
    parameters: Dict[str, Any]
):
    """
    ValueSet $validate-code operation (POST version).
    """
    try:
        url = None
        code = None
        system = None
        display = None
        coding = None

        for param in parameters.get("parameter", []):
            name = param.get("name")
            if name == "url":
                url = param.get("valueUri")
            elif name == "code":
                code = param.get("valueCode")
            elif name == "system":
                system = param.get("valueUri")
            elif name == "display":
                display = param.get("valueString")
            elif name == "coding":
                coding = param.get("valueCoding")

        result = terminology_service.validate_code(
            url=url,
            code=code,
            system=system,
            display=display,
            coding=coding
        )

        return JSONResponse(content=result)

    except Exception as e:
        logger.error(f"Error in ValueSet/$validate-code: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/ConceptMap/$translate",
    summary="Translate a code"
)
async def conceptmap_translate(
    url: str = Query(..., description="ConceptMap URL"),
    code: str = Query(..., description="Code to translate"),
    system: Optional[str] = Query(None, description="Source code system")
):
    """
    ConceptMap $translate operation.

    Translate a code from one code system to another.
    """
    try:
        result = terminology_service.translate(
            url=url,
            code=code,
            system=system
        )

        return JSONResponse(content=result)

    except Exception as e:
        logger.error(f"Error in ConceptMap/$translate: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post(
    "/ConceptMap/$translate",
    summary="Translate a code (POST)"
)
async def conceptmap_translate_post(
    parameters: Dict[str, Any]
):
    """
    ConceptMap $translate operation (POST version).
    """
    try:
        url = None
        code = None
        system = None
        coding = None

        for param in parameters.get("parameter", []):
            name = param.get("name")
            if name == "url":
                url = param.get("valueUri")
            elif name == "code":
                code = param.get("valueCode")
            elif name == "system":
                system = param.get("valueUri")
            elif name == "coding":
                coding = param.get("valueCoding")

        result = terminology_service.translate(
            url=url,
            code=code,
            system=system,
            coding=coding
        )

        return JSONResponse(content=result)

    except Exception as e:
        logger.error(f"Error in ConceptMap/$translate: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/CodeSystem/$subsumes",
    summary="Test subsumption between codes"
)
async def codesystem_subsumes(
    system: str = Query(..., description="Code system URL"),
    codeA: str = Query(..., description="First code"),
    codeB: str = Query(..., description="Second code")
):
    """
    CodeSystem $subsumes operation.

    Test if code A subsumes code B (A is-a B).
    """
    try:
        result = terminology_service.subsumes(
            system=system,
            code_a=codeA,
            code_b=codeB
        )

        return JSONResponse(content=result)

    except Exception as e:
        logger.error(f"Error in CodeSystem/$subsumes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# ============================================================================
# SUBSCRIPTION MANAGEMENT
# ============================================================================

@router.post(
    "/Subscription",
    summary="Create a subscription",
    status_code=status.HTTP_201_CREATED
)
async def create_subscription(
    subscription: Dict[str, Any],
    tenant_id: UUID = Depends(get_tenant_id)
):
    """
    Create a new FHIR Subscription for real-time notifications.
    """
    try:
        # Parse subscription from FHIR resource
        criteria = subscription.get("criteria", "")
        channel = subscription.get("channel", {})
        channel_type = ChannelType(channel.get("type", "rest-hook"))
        endpoint = channel.get("endpoint", "")
        payload = channel.get("payload", "application/fhir+json")
        headers = channel.get("header", [])
        reason = subscription.get("reason", "")

        created = await subscription_service.create_subscription(
            tenant_id=str(tenant_id),
            criteria=criteria,
            channel_type=channel_type,
            endpoint=endpoint,
            reason=reason,
            payload=payload,
            headers=headers
        )

        result = subscription_service.to_fhir_resource(created)

        return JSONResponse(
            content=result,
            status_code=status.HTTP_201_CREATED,
            headers={"Location": f"/fhir/Subscription/{created.subscription_id}"}
        )

    except Exception as e:
        logger.error(f"Error creating subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/Subscription/{subscription_id}",
    summary="Get a subscription"
)
async def get_subscription(
    subscription_id: str
):
    """
    Get a subscription by ID.
    """
    try:
        subscription = await subscription_service.get_subscription(subscription_id)

        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subscription/{subscription_id} not found"
            )

        result = subscription_service.to_fhir_resource(subscription)
        return JSONResponse(content=result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.delete(
    "/Subscription/{subscription_id}",
    summary="Delete a subscription",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_subscription(
    subscription_id: str
):
    """
    Delete a subscription.
    """
    try:
        deleted = await subscription_service.delete_subscription(subscription_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subscription/{subscription_id} not found"
            )

        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/Subscription",
    summary="Search subscriptions"
)
async def search_subscriptions(
    status: Optional[str] = Query(None, description="Filter by status"),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """
    Search for subscriptions.
    """
    try:
        from .services.subscription_service import SubscriptionStatus

        sub_status = None
        if status:
            try:
                sub_status = SubscriptionStatus(status)
            except ValueError:
                pass

        subscriptions = await subscription_service.get_tenant_subscriptions(
            tenant_id=str(tenant_id),
            status=sub_status
        )

        bundle = {
            "resourceType": "Bundle",
            "type": "searchset",
            "total": len(subscriptions),
            "entry": [
                {
                    "fullUrl": f"/fhir/Subscription/{s.subscription_id}",
                    "resource": subscription_service.to_fhir_resource(s),
                    "search": {"mode": "match"}
                }
                for s in subscriptions
            ]
        }

        return JSONResponse(content=bundle)

    except Exception as e:
        logger.error(f"Error searching subscriptions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# ============================================================================
# EXPORT ALL ROUTERS
# ============================================================================

__all__ = ["router"]

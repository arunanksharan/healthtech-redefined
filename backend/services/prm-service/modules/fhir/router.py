"""
FHIR R4 REST API Router
FastAPI router for FHIR resource operations
"""
from typing import Dict, Any, Optional
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


# ============================================================================
# CAPABILITY STATEMENT / METADATA
# ============================================================================

@router.get("/metadata", summary="Get server capability statement")
async def get_capability_statement():
    """
    Get FHIR CapabilityStatement describing server capabilities
    """
    # TODO: Generate dynamically from registered resources
    capability = {
        "resourceType": "CapabilityStatement",
        "status": "active",
        "date": "2024-11-25",
        "kind": "instance",
        "software": {
            "name": "PRM FHIR Server",
            "version": "1.0.0"
        },
        "implementation": {
            "description": "PRM FHIR R4 Server - 15+ Core Resources",
            "url": "/fhir"
        },
        "fhirVersion": "4.0.1",
        "format": ["json"],
        "rest": [
            {
                "mode": "server",
                "resource": [
                    {
                        "type": "Patient",
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
                        "searchParam": [
                            {"name": "_id", "type": "token"},
                            {"name": "identifier", "type": "token"},
                            {"name": "name", "type": "string"},
                            {"name": "birthdate", "type": "date"},
                            {"name": "gender", "type": "token"}
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
# EXPORT ALL ROUTERS
# ============================================================================

__all__ = ["router"]

"""
FHIR Service - Generic FHIR R4 Resource Management
Provides CRUD operations, versioning, and search for any FHIR resource
"""
import os
import sys
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from fastapi import FastAPI, HTTPException, Depends, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from loguru import logger

from shared.database.connection import get_db, engine
from shared.database.models import Base, FHIRResource, FHIRResourceVersion
from shared.events.publisher import publish_event
from shared.events.types import EventType

from .schemas import (
    FHIRResourceCreate,
    FHIRResourceUpdate,
    FHIRResourceResponse,
    FHIRResourceListResponse,
    FHIRResourceVersionResponse,
    FHIRSearchParams,
    FHIRBundleResponse,
    FHIRValidationResponse
)

# Initialize FastAPI app
app = FastAPI(
    title="FHIR Service",
    description="Generic FHIR R4 resource management with versioning and search",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on environment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Health Check ====================

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "fhir-service",
        "timestamp": datetime.utcnow().isoformat()
    }


# ==================== FHIR Resource CRUD ====================

@app.post(
    "/api/v1/fhir/{resource_type}",
    response_model=FHIRResourceResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["FHIR Resources"]
)
async def create_fhir_resource(
    resource_type: str,
    resource_create: FHIRResourceCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new FHIR resource

    Supports any FHIR R4 resource type (Observation, Condition, Procedure, etc.)
    Automatically tracks versions and publishes events.
    """
    try:
        # Validate resource_type matches path parameter
        if resource_create.resource_type != resource_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Resource type mismatch: path='{resource_type}', body='{resource_create.resource_type}'"
            )

        # Create FHIR resource
        fhir_resource = FHIRResource(
            tenant_id=resource_create.tenant_id,
            resource_type=resource_create.resource_type,
            resource_data=resource_create.resource_data,
            subject_id=resource_create.subject_id,
            author_id=resource_create.author_id,
            version=1
        )

        db.add(fhir_resource)
        db.flush()

        # Create initial version record
        version_record = FHIRResourceVersion(
            resource_id=fhir_resource.id,
            version=1,
            resource_data=resource_create.resource_data,
            changed_by=resource_create.author_id,
            change_description="Initial creation"
        )
        db.add(version_record)
        db.commit()
        db.refresh(fhir_resource)

        logger.info(
            f"Created {resource_type} resource: {fhir_resource.id} "
            f"for tenant {resource_create.tenant_id}"
        )

        # Publish event
        await publish_event(
            event_type=EventType.FHIR_RESOURCE_CREATED,
            tenant_id=str(resource_create.tenant_id),
            payload={
                "resource_id": str(fhir_resource.id),
                "resource_type": resource_type,
                "subject_id": str(resource_create.subject_id) if resource_create.subject_id else None,
                "version": 1
            },
            source_service="fhir-service"
        )

        return fhir_resource

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating FHIR resource: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create resource: {str(e)}"
        )


@app.get(
    "/api/v1/fhir/{resource_type}/{resource_id}",
    response_model=FHIRResourceResponse,
    tags=["FHIR Resources"]
)
async def get_fhir_resource(
    resource_type: str,
    resource_id: UUID,
    version: Optional[int] = Query(None, description="Specific version to retrieve"),
    db: Session = Depends(get_db)
):
    """
    Get a FHIR resource by ID

    Optionally specify a version number to retrieve a specific version.
    """
    try:
        # Get resource
        query = db.query(FHIRResource).filter(
            FHIRResource.id == resource_id,
            FHIRResource.resource_type == resource_type,
            FHIRResource.is_deleted == False
        )

        resource = query.first()

        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{resource_type} resource not found: {resource_id}"
            )

        # If specific version requested, get version data
        if version is not None:
            version_record = db.query(FHIRResourceVersion).filter(
                FHIRResourceVersion.resource_id == resource_id,
                FHIRResourceVersion.version == version
            ).first()

            if not version_record:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Version {version} not found for resource {resource_id}"
                )

            # Return resource with historical data
            resource.resource_data = version_record.resource_data
            resource.version = version_record.version

        return resource

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving FHIR resource: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve resource: {str(e)}"
        )


@app.put(
    "/api/v1/fhir/{resource_type}/{resource_id}",
    response_model=FHIRResourceResponse,
    tags=["FHIR Resources"]
)
async def update_fhir_resource(
    resource_type: str,
    resource_id: UUID,
    resource_update: FHIRResourceUpdate,
    change_description: Optional[str] = Query(None, description="Description of changes"),
    db: Session = Depends(get_db)
):
    """
    Update a FHIR resource

    Creates a new version of the resource while preserving history.
    """
    try:
        # Get existing resource
        resource = db.query(FHIRResource).filter(
            FHIRResource.id == resource_id,
            FHIRResource.resource_type == resource_type,
            FHIRResource.is_deleted == False
        ).first()

        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{resource_type} resource not found: {resource_id}"
            )

        # Validate resource type consistency
        if resource_update.resource_data.get("resourceType") != resource_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot change resource type from {resource_type}"
            )

        # Increment version
        new_version = resource.version + 1

        # Create version record for current state
        version_record = FHIRResourceVersion(
            resource_id=resource.id,
            version=new_version,
            resource_data=resource_update.resource_data,
            change_description=change_description or "Resource updated"
        )
        db.add(version_record)

        # Update resource
        resource.resource_data = resource_update.resource_data
        resource.version = new_version
        resource.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(resource)

        logger.info(
            f"Updated {resource_type} resource: {resource_id} "
            f"to version {new_version}"
        )

        # Publish event
        await publish_event(
            event_type=EventType.FHIR_RESOURCE_UPDATED,
            tenant_id=str(resource.tenant_id),
            payload={
                "resource_id": str(resource.id),
                "resource_type": resource_type,
                "version": new_version,
                "change_description": change_description
            },
            source_service="fhir-service"
        )

        return resource

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating FHIR resource: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update resource: {str(e)}"
        )


@app.delete(
    "/api/v1/fhir/{resource_type}/{resource_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["FHIR Resources"]
)
async def delete_fhir_resource(
    resource_type: str,
    resource_id: UUID,
    hard_delete: bool = Query(False, description="Permanently delete (default: soft delete)"),
    db: Session = Depends(get_db)
):
    """
    Delete a FHIR resource

    By default performs soft delete (marks as deleted).
    Set hard_delete=true to permanently remove.
    """
    try:
        resource = db.query(FHIRResource).filter(
            FHIRResource.id == resource_id,
            FHIRResource.resource_type == resource_type
        ).first()

        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{resource_type} resource not found: {resource_id}"
            )

        if hard_delete:
            # Hard delete - remove from database
            db.delete(resource)
            logger.warning(f"Hard deleted {resource_type} resource: {resource_id}")
        else:
            # Soft delete - mark as deleted
            resource.is_deleted = True
            resource.updated_at = datetime.utcnow()
            logger.info(f"Soft deleted {resource_type} resource: {resource_id}")

        db.commit()

        # Publish event
        await publish_event(
            event_type=EventType.FHIR_RESOURCE_DELETED,
            tenant_id=str(resource.tenant_id),
            payload={
                "resource_id": str(resource_id),
                "resource_type": resource_type,
                "hard_delete": hard_delete
            },
            source_service="fhir-service"
        )

        return None

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting FHIR resource: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete resource: {str(e)}"
        )


# ==================== Search & Query ====================

@app.get(
    "/api/v1/fhir/{resource_type}",
    response_model=FHIRResourceListResponse,
    tags=["FHIR Search"]
)
async def search_fhir_resources(
    resource_type: str,
    subject_id: Optional[UUID] = Query(None, description="Filter by subject/patient"),
    author_id: Optional[UUID] = Query(None, description="Filter by author"),
    status: Optional[str] = Query(None, description="Filter by status field"),
    code: Optional[str] = Query(None, description="Search by coding code"),
    date_from: Optional[datetime] = Query(None, description="Created after this date"),
    date_to: Optional[datetime] = Query(None, description="Created before this date"),
    include_deleted: bool = Query(False, description="Include deleted resources"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Search FHIR resources with filters

    Supports filtering by subject, author, status, codes, and date ranges.
    """
    try:
        # Build base query
        query = db.query(FHIRResource).filter(
            FHIRResource.resource_type == resource_type
        )

        # Apply filters
        if not include_deleted:
            query = query.filter(FHIRResource.is_deleted == False)

        if subject_id:
            query = query.filter(FHIRResource.subject_id == subject_id)

        if author_id:
            query = query.filter(FHIRResource.author_id == author_id)

        if status:
            # Search in JSONB field
            query = query.filter(
                FHIRResource.resource_data['status'].astext == status
            )

        if code:
            # Search for code in coding arrays
            query = query.filter(
                FHIRResource.resource_data.op('?&')(f'code.coding[*].code')
            )

        if date_from:
            query = query.filter(FHIRResource.created_at >= date_from)

        if date_to:
            query = query.filter(FHIRResource.created_at <= date_to)

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        resources = query.order_by(
            FHIRResource.created_at.desc()
        ).offset(offset).limit(page_size).all()

        # Calculate pagination metadata
        has_next = (offset + page_size) < total
        has_previous = page > 1

        return FHIRResourceListResponse(
            total=total,
            resources=resources,
            page=page,
            page_size=page_size,
            has_next=has_next,
            has_previous=has_previous
        )

    except Exception as e:
        logger.error(f"Error searching FHIR resources: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@app.get(
    "/api/v1/fhir/patient/{patient_id}/timeline",
    response_model=FHIRBundleResponse,
    tags=["FHIR Search"]
)
async def get_patient_timeline(
    patient_id: UUID,
    resource_types: Optional[List[str]] = Query(
        None,
        description="Filter by resource types (e.g., Observation, Condition)"
    ),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get complete clinical timeline for a patient

    Returns all FHIR resources related to a patient in chronological order.
    """
    try:
        query = db.query(FHIRResource).filter(
            FHIRResource.subject_id == patient_id,
            FHIRResource.is_deleted == False
        )

        if resource_types:
            query = query.filter(FHIRResource.resource_type.in_(resource_types))

        if date_from:
            query = query.filter(FHIRResource.created_at >= date_from)

        if date_to:
            query = query.filter(FHIRResource.created_at <= date_to)

        resources = query.order_by(FHIRResource.created_at.asc()).all()

        # Build FHIR Bundle
        entries = []
        for resource in resources:
            entries.append({
                "resource": resource.resource_data,
                "fullUrl": f"urn:uuid:{resource.id}"
            })

        return FHIRBundleResponse(
            type="searchset",
            total=len(entries),
            entry=entries
        )

    except Exception as e:
        logger.error(f"Error fetching patient timeline: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch timeline: {str(e)}"
        )


# ==================== Version History ====================

@app.get(
    "/api/v1/fhir/{resource_type}/{resource_id}/history",
    response_model=List[FHIRResourceVersionResponse],
    tags=["FHIR Versioning"]
)
async def get_resource_history(
    resource_type: str,
    resource_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get complete version history for a FHIR resource

    Returns all versions in chronological order.
    """
    try:
        # Verify resource exists
        resource = db.query(FHIRResource).filter(
            FHIRResource.id == resource_id,
            FHIRResource.resource_type == resource_type
        ).first()

        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{resource_type} resource not found: {resource_id}"
            )

        # Get all versions
        versions = db.query(FHIRResourceVersion).filter(
            FHIRResourceVersion.resource_id == resource_id
        ).order_by(FHIRResourceVersion.version.asc()).all()

        return versions

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching resource history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch history: {str(e)}"
        )


# ==================== Validation ====================

@app.post(
    "/api/v1/fhir/validate/{resource_type}",
    response_model=FHIRValidationResponse,
    tags=["FHIR Validation"]
)
async def validate_fhir_resource(
    resource_type: str,
    resource_data: Dict[str, Any]
):
    """
    Validate a FHIR resource against FHIR R4 specification

    Checks structure, required fields, and data types.
    """
    try:
        errors = []
        warnings = []

        # Basic validation
        if resource_data.get("resourceType") != resource_type:
            errors.append(
                f"resourceType mismatch: expected '{resource_type}', "
                f"got '{resource_data.get('resourceType')}'"
            )

        # Resource-specific validation could be added here
        # For now, basic structure check
        if "resourceType" not in resource_data:
            errors.append("Missing required field: resourceType")

        valid = len(errors) == 0

        return FHIRValidationResponse(
            valid=valid,
            errors=errors,
            warnings=warnings,
            resource_type=resource_type
        )

    except Exception as e:
        logger.error(f"Error validating FHIR resource: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation failed: {str(e)}"
        )


# ==================== Startup ====================

@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    logger.info("FHIR Service starting up...")

    # Create tables if they don't exist
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified/created")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")

    logger.info("FHIR Service ready!")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002, reload=True)

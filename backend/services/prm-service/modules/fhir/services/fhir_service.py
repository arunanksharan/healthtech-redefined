"""
FHIR Service Layer
Business logic for FHIR resource operations
"""
from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from loguru import logger

from ..repository.fhir_repository import FHIRRepository
from ..validators.validator import FHIRValidator, ValidationResult


class FHIRService:
    """
    Service layer for FHIR operations
    Handles business logic and coordinates between validators and repository
    """
    
    def __init__(self, db: Session):
        """
        Initialize FHIR service
        
        Args:
            db: Database session
        """
        self.db = db
        self.repository = FHIRRepository(db)
        self.validator = FHIRValidator()
    
    def create_resource(
        self,
        tenant_id: UUID,
        resource: Dict[str, Any],
        validate: bool = True
    ) -> Dict[str, Any]:
        """
        Create a new FHIR resource
        
        Args:
            tenant_id: Tenant identifier
            resource: FHIR resource data
            validate: Whether to validate before creating
            
        Returns:
            Created resource with metadata
            
        Raises:
            ValueError: If validation fails
        """
        # Validate resource
        if validate:
            validation_result = self.validator.validate(resource)
            if not validation_result.valid:
                logger.error(f"Validation failed: {validation_result.errors}")
                raise ValueError(
                    f"Resource validation failed: {validation_result.to_operation_outcome()}"
                )
        
        # Extract resource type
        resource_type = resource.get("resourceType")
        if not resource_type:
            raise ValueError("Resource must have a resourceType")
        
        # Create resource
        try:
            created = self.repository.create(
                tenant_id=tenant_id,
                resource_type=resource_type,
                resource_data=resource
            )
            
            logger.info(f"Created {resource_type} resource: {created.get('id')}")
            return created
            
        except Exception as e:
            logger.error(f"Error creating resource: {e}")
            raise
    
    def get_resource(
        self,
        tenant_id: UUID,
        resource_type: str,
        resource_id: str,
        version: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get a FHIR resource by ID
        
        Args:
            tenant_id: Tenant identifier
            resource_type: Type of resource
            resource_id: Resource ID
            version: Optional version number
            
        Returns:
            FHIR resource or None if not found
        """
        try:
            resource = self.repository.get_by_id(
                tenant_id=tenant_id,
                resource_type=resource_type,
                resource_id=resource_id,
                version=version
            )
            
            if resource:
                logger.debug(f"Retrieved {resource_type}/{resource_id}")
            else:
                logger.debug(f"Resource not found: {resource_type}/{resource_id}")
            
            return resource
            
        except Exception as e:
            logger.error(f"Error retrieving resource: {e}")
            raise
    
    def update_resource(
        self,
        tenant_id: UUID,
        resource_type: str,
        resource_id: str,
        resource: Dict[str, Any],
        validate: bool = True
    ) -> Dict[str, Any]:
        """
        Update a FHIR resource
        
        Args:
            tenant_id: Tenant identifier
            resource_type: Type of resource
            resource_id: Resource ID
            resource: Updated resource data
            validate: Whether to validate before updating
            
        Returns:
            Updated resource with new version
            
        Raises:
            ValueError: If validation fails or resource not found
        """
        # Validate resource
        if validate:
            validation_result = self.validator.validate(resource)
            if not validation_result.valid:
                logger.error(f"Validation failed: {validation_result.errors}")
                raise ValueError(
                    f"Resource validation failed: {validation_result.to_operation_outcome()}"
                )
        
        # Ensure resource type and ID match
        if resource.get("resourceType") != resource_type:
            raise ValueError("Resource type in body must match URL")
        
        # Update resource
        try:
            updated = self.repository.update(
                tenant_id=tenant_id,
                resource_type=resource_type,
                resource_id=resource_id,
                resource_data=resource
            )
            
            logger.info(f"Updated {resource_type}/{resource_id}")
            return updated
            
        except Exception as e:
            logger.error(f"Error updating resource: {e}")
            raise
    
    def delete_resource(
        self,
        tenant_id: UUID,
        resource_type: str,
        resource_id: str
    ) -> bool:
        """
        Delete a FHIR resource (soft delete)
        
        Args:
            tenant_id: Tenant identifier
            resource_type: Type of resource
            resource_id: Resource ID
            
        Returns:
            True if deleted successfully
        """
        try:
            deleted = self.repository.delete(
                tenant_id=tenant_id,
                resource_type=resource_type,
                resource_id=resource_id
            )
            
            if deleted:
                logger.info(f"Deleted {resource_type}/{resource_id}")
            else:
                logger.warning(f"Resource not found for deletion: {resource_type}/{resource_id}")
            
            return deleted
            
        except Exception as e:
            logger.error(f"Error deleting resource: {e}")
            raise
    
    def search_resources(
        self,
        tenant_id: UUID,
        resource_type: str,
        search_params: Dict[str, Any],
        count: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Search for FHIR resources
        
        Args:
            tenant_id: Tenant identifier
            resource_type: Type of resource
            search_params: Search parameters
            count: Number of results to return
            offset: Offset for pagination
            
        Returns:
            FHIR Bundle with search results
        """
        try:
            bundle = self.repository.search(
                tenant_id=tenant_id,
                resource_type=resource_type,
                search_params=search_params,
                limit=count,
                offset=offset
            )
            
            logger.debug(f"Search {resource_type}: {bundle.get('total', 0)} results")
            return bundle
            
        except Exception as e:
            logger.error(f"Error searching resources: {e}")
            raise
    
    def get_resource_history(
        self,
        tenant_id: UUID,
        resource_type: str,
        resource_id: str
    ) -> Dict[str, Any]:
        """
        Get version history for a resource
        
        Args:
            tenant_id: Tenant identifier
            resource_type: Type of resource
            resource_id: Resource ID
            
        Returns:
            FHIR Bundle with history entries
        """
        try:
            versions = self.repository.get_history(
                tenant_id=tenant_id,
                resource_type=resource_type,
                resource_id=resource_id
            )
            
            # Build history bundle
            bundle = {
                "resourceType": "Bundle",
                "type": "history",
                "total": len(versions),
                "entry": []
            }
            
            for version in versions:
                bundle["entry"].append({
                    "fullUrl": f"/fhir/{resource_type}/{resource_id}/_history/{version.get('meta', {}).get('versionId', '1')}",
                    "resource": version,
                    "request": {
                        "method": "GET",
                        "url": f"{resource_type}/{resource_id}"
                    },
                    "response": {
                        "status": "200 OK",
                        "lastModified": version.get("meta", {}).get("lastUpdated")
                    }
                })
            
            logger.debug(f"Retrieved history for {resource_type}/{resource_id}: {len(versions)} versions")
            return bundle
            
        except Exception as e:
            logger.error(f"Error retrieving resource history: {e}")
            raise
    
    def validate_resource(
        self,
        resource: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate a FHIR resource without persisting
        
        Args:
            resource: FHIR resource to validate
            
        Returns:
            OperationOutcome with validation results
        """
        validation_result = self.validator.validate(resource)
        return validation_result.to_operation_outcome()
    
    def validate_bundle(
        self,
        bundle: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate a FHIR Bundle
        
        Args:
            bundle: FHIR Bundle to validate
            
        Returns:
            OperationOutcome with validation results
        """
        validation_result = self.validator.validate_bundle(bundle)
        return validation_result.to_operation_outcome()

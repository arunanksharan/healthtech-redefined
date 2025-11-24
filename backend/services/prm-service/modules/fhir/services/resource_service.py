"""
FHIR Resource Service
Business logic layer for FHIR resource operations
"""

from typing import Dict, Any, List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from loguru import logger

from ..repository.fhir_repository import FHIRRepository
from ..models import Patient, Practitioner, Organization, Encounter, Observation, Condition
from .validation_service import FHIRValidationService


class FHIRResourceService:
    """Service for FHIR resource operations with validation"""

    # Map resource types to Pydantic models
    RESOURCE_MODELS = {
        "Patient": Patient,
        "Practitioner": Practitioner,
        "Organization": Organization,
        "Encounter": Encounter,
        "Observation": Observation,
        "Condition": Condition,
    }

    def __init__(self, db: Session):
        self.repository = FHIRRepository(db)
        self.validator = FHIRValidationService()

    def create_resource(
        self,
        tenant_id: UUID,
        resource_type: str,
        resource_data: Dict[str, Any],
        validate: bool = True
    ) -> Dict[str, Any]:
        """
        Create a new FHIR resource with validation
        
        Args:
            tenant_id: Tenant identifier
            resource_type: Type of FHIR resource
            resource_data: Resource data
            validate: Whether to validate the resource
            
        Returns:
            Created resource
            
        Raises:
            ValueError: If validation fails or resource type unknown
        """
        try:
            # Validate resource type
            if resource_type not in self.RESOURCE_MODELS:
                raise ValueError(f"Unknown resource type: {resource_type}")

            # Validate resource structure if requested
            if validate:
                validation_result = self.validator.validate_resource(
                    resource_type,
                    resource_data
                )
                
                if not validation_result["valid"]:
                    error_msgs = [e["message"] for e in validation_result["errors"]]
                    raise ValueError(f"Validation failed: {', '.join(error_msgs)}")

            # Create resource
            created = self.repository.create(
                tenant_id=tenant_id,
                resource_type=resource_type,
                resource_data=resource_data
            )

            logger.info(f"Created {resource_type} resource: {created.get('id')}")
            
            return created

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error creating resource: {e}")
            raise ValueError(f"Failed to create resource: {str(e)}")

    def get_resource(
        self,
        tenant_id: UUID,
        resource_type: str,
        resource_id: str,
        version: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get FHIR resource by ID
        
        Args:
            tenant_id: Tenant identifier
            resource_type: Type of FHIR resource
            resource_id: Resource ID
            version: Specific version (optional)
            
        Returns:
            Resource or None if not found
        """
        try:
            resource = self.repository.get_by_id(
                tenant_id=tenant_id,
                resource_type=resource_type,
                resource_id=resource_id,
                version=version
            )

            return resource

        except Exception as e:
            logger.error(f"Error retrieving resource: {e}")
            raise ValueError(f"Failed to retrieve resource: {str(e)}")

    def update_resource(
        self,
        tenant_id: UUID,
        resource_type: str,
        resource_id: str,
        resource_data: Dict[str, Any],
        validate: bool = True
    ) -> Dict[str, Any]:
        """
        Update FHIR resource with validation
        
        Args:
            tenant_id: Tenant identifier
            resource_type: Type of FHIR resource
            resource_id: Resource ID
            resource_data: Updated resource data
            validate: Whether to validate the resource
            
        Returns:
            Updated resource
            
        Raises:
            ValueError: If validation fails or resource not found
        """
        try:
            # Validate resource type
            if resource_type not in self.RESOURCE_MODELS:
                raise ValueError(f"Unknown resource type: {resource_type}")

            # Ensure IDs match
            if resource_data.get("id") and resource_data.get("id") != resource_id:
                raise ValueError("Resource ID in body does not match URL")

            # Validate resource structure if requested
            if validate:
                validation_result = self.validator.validate_resource(
                    resource_type,
                    resource_data
                )
                
                if not validation_result["valid"]:
                    error_msgs = [e["message"] for e in validation_result["errors"]]
                    raise ValueError(f"Validation failed: {', '.join(error_msgs)}")

            # Update resource
            updated = self.repository.update(
                tenant_id=tenant_id,
                resource_type=resource_type,
                resource_id=resource_id,
                resource_data=resource_data
            )

            logger.info(f"Updated {resource_type} resource: {resource_id}")
            
            return updated

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error updating resource: {e}")
            raise ValueError(f"Failed to update resource: {str(e)}")

    def delete_resource(
        self,
        tenant_id: UUID,
        resource_type: str,
        resource_id: str
    ) -> bool:
        """
        Delete FHIR resource
        
        Args:
            tenant_id: Tenant identifier
            resource_type: Type of FHIR resource
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
                logger.info(f"Deleted {resource_type} resource: {resource_id}")
            else:
                logger.warning(f"Resource not found for deletion: {resource_type}/{resource_id}")

            return deleted

        except Exception as e:
            logger.error(f"Error deleting resource: {e}")
            raise ValueError(f"Failed to delete resource: {str(e)}")

    def search_resources(
        self,
        tenant_id: UUID,
        resource_type: str,
        search_params: Dict[str, Any],
        count: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Search FHIR resources
        
        Args:
            tenant_id: Tenant identifier
            resource_type: Type of FHIR resource
            search_params: Search parameters
            count: Number of results per page
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

            return bundle

        except Exception as e:
            logger.error(f"Error searching resources: {e}")
            raise ValueError(f"Failed to search resources: {str(e)}")

    def get_resource_history(
        self,
        tenant_id: UUID,
        resource_type: str,
        resource_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get version history for a resource
        
        Args:
            tenant_id: Tenant identifier
            resource_type: Type of FHIR resource
            resource_id: Resource ID
            
        Returns:
            List of all versions
        """
        try:
            history = self.repository.get_history(
                tenant_id=tenant_id,
                resource_type=resource_type,
                resource_id=resource_id
            )

            return history

        except Exception as e:
            logger.error(f"Error retrieving resource history: {e}")
            raise ValueError(f"Failed to retrieve history: {str(e)}")

    def validate_resource_data(
        self,
        resource_type: str,
        resource_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate resource without persisting
        
        Args:
            resource_type: Type of FHIR resource
            resource_data: Resource data to validate
            
        Returns:
            Validation result
        """
        try:
            return self.validator.validate_resource(resource_type, resource_data)
        except Exception as e:
            logger.error(f"Error validating resource: {e}")
            raise ValueError(f"Validation error: {str(e)}")

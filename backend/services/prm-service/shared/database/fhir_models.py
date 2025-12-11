"""
FHIR R4 Database Models
Database models for storing FHIR resources
"""
from datetime import datetime
import uuid
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID, TSVECTOR
from sqlalchemy.ext.declarative import declarative_base

# Use the same Base as the main models
from .models import Base


def generate_uuid() -> uuid.UUID:
    """Generate a new UUID4"""
    return uuid.uuid4()


# ============================================================================
# FHIR RESOURCE STORAGE
# ============================================================================


class FHIRResource(Base):
    """
    Generic FHIR resource storage
    Stores all FHIR resources in a single table using JSONB for flexibility
    """
    __tablename__ = "fhir_resources"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    
    # Tenant for multi-tenancy
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Resource type (Patient, Practitioner, Observation, etc.)
    resource_type = Column(String(50), nullable=False)
    
    # FHIR resource ID (unique within resource_type and tenant)
    fhir_id = Column(String(64), nullable=False)
    
    # Version control
    version_id = Column(Integer, nullable=False, default=1)
    last_updated = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # JSONB storage for the complete FHIR resource
    resource_data = Column(JSONB, nullable=False)
    
    # Search optimization - extracted tokens for common search parameters
    # Format: {"identifier": ["MRN12345", ...], "name": ["John", "Smith"], ...}
    search_tokens = Column(JSONB, default=dict)
    
    # Full-text search - extracted searchable strings
    search_strings = Column(TSVECTOR)
    
    # Metadata
    deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        # Unique constraint on tenant, resource_type, fhir_id (for current version)
        Index("idx_fhir_resources_unique", "tenant_id", "resource_type", "fhir_id", unique=True, postgresql_where=(deleted == False)),
        
        # Search indexes
        Index("idx_fhir_resources_tenant_type", "tenant_id", "resource_type"),
        Index("idx_fhir_resources_fhir_id", "fhir_id"),
        Index("idx_fhir_resources_type", "resource_type"),
        Index("idx_fhir_resources_deleted", "deleted"),
        Index("idx_fhir_resources_last_updated", "last_updated"),
        
        # GIN index for JSONB search optimization
        Index("idx_fhir_resources_data", "resource_data", postgresql_using="gin"),
        Index("idx_fhir_resources_search_tokens", "search_tokens", postgresql_using="gin"),
        
        # Full-text search index
        Index("idx_fhir_resources_search_strings", "search_strings", postgresql_using="gin"),
    )


class FHIRResourceHistory(Base):
    """
    Version history for FHIR resources
    Tracks all changes to FHIR resources
    """
    __tablename__ = "fhir_resource_history"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    
    # Reference to the current resource
    resource_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Tenant
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Resource identification
    resource_type = Column(String(50), nullable=False)
    fhir_id = Column(String(64), nullable=False)
    
    # Version information
    version_id = Column(Integer, nullable=False)
    
    # Snapshot of the resource at this version
    resource_data = Column(JSONB, nullable=False)
    
    # Operation that created this version
    operation = Column(String(10), nullable=False)  # create, update, delete
    
    # Change metadata
    changed_by = Column(String(255))  # User or system that made the change
    change_reason = Column(Text)  # Optional reason for the change
    changed_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index("idx_fhir_history_resource", "resource_id"),
        Index("idx_fhir_history_tenant_type_id", "tenant_id", "resource_type", "fhir_id"),
        Index("idx_fhir_history_version", "resource_id", "version_id"),
        Index("idx_fhir_history_changed_at", "changed_at"),
    )


# ============================================================================
# FHIR TERMINOLOGY STORAGE
# ============================================================================


class FHIRCodeSystem(Base):
    """
    FHIR CodeSystem resource storage
    Stores terminology code systems (SNOMED, LOINC, ICD-10, etc.)
    """
    __tablename__ = "fhir_code_systems"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    
    # CodeSystem identification
    url = Column(String(255), nullable=False, unique=True)
    version = Column(String(50))
    name = Column(String(255), nullable=False)
    title = Column(String(500))
    status = Column(String(20), nullable=False)  # draft, active, retired
    
    # Content
    content = Column(String(20), nullable=False)  # not-present, example, fragment, complete
    count = Column(Integer)  # Number of concepts
    
    # Full CodeSystem resource
    resource_data = Column(JSONB, nullable=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index("idx_fhir_codesystems_tenant", "tenant_id"),
        Index("idx_fhir_codesystems_url", "url"),
        Index("idx_fhir_codesystems_status", "status"),
    )


class FHIRValueSet(Base):
    """
    FHIR ValueSet resource storage
    Stores value sets for coded values
    """
    __tablename__ = "fhir_value_sets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    
    # ValueSet identification
    url = Column(String(255), nullable=False, unique=True)
    version = Column(String(50))
    name = Column(String(255), nullable=False)
    title = Column(String(500))
    status = Column(String(20), nullable=False)  # draft, active, retired
    
    # Expansion (pre-computed if available)
    expansion_data = Column(JSONB)  # Cached expansion
    expansion_timestamp = Column(DateTime(timezone=True))
    
    # Full ValueSet resource
    resource_data = Column(JSONB, nullable=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index("idx_fhir_valuesets_tenant", "tenant_id"),
        Index("idx_fhir_valuesets_url", "url"),
        Index("idx_fhir_valuesets_status", "status"),
    )


class FHIRConceptMap(Base):
    """
    FHIR ConceptMap resource storage
    Stores mappings between code systems
    """
    __tablename__ = "fhir_concept_maps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    
    # ConceptMap identification
    url = Column(String(255), nullable=False, unique=True)
    version = Column(String(50))
    name = Column(String(255), nullable=False)
    title = Column(String(500))
    status = Column(String(20), nullable=False)  # draft, active, retired
    
    # Source and target
    source_url = Column(String(255))
    target_url = Column(String(255))
    
    # Full ConceptMap resource
    resource_data = Column(JSONB, nullable=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index("idx_fhir_conceptmaps_tenant", "tenant_id"),
        Index("idx_fhir_conceptmaps_url", "url"),
        Index("idx_fhir_conceptmaps_source_target", "source_url", "target_url"),
    )


# ============================================================================
# FHIR SUBSCRIPTIONS
# ============================================================================


class FHIRSubscription(Base):
    """
    FHIR Subscription storage
    Tracks active subscriptions for resource notifications
    """
    __tablename__ = "fhir_subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Subscription details
    fhir_id = Column(String(64), nullable=False)
    status = Column(String(20), nullable=False)  # requested, active, error, off
    
    # Criteria
    criteria = Column(Text, nullable=False)  # FHIR search criteria
    resource_type = Column(String(50))  # Extracted from criteria
    
    # Channel
    channel_type = Column(String(20), nullable=False)  # rest-hook, websocket, email
    channel_endpoint = Column(String(500))  # URL or endpoint
    channel_payload = Column(String(20), nullable=False, default="application/fhir+json")
    channel_headers = Column(JSONB)  # Custom headers
    
    # Error tracking
    error_count = Column(Integer, nullable=False, default=0)
    last_error = Column(Text)
    last_error_at = Column(DateTime(timezone=True))
    
    # Delivery tracking
    last_triggered_at = Column(DateTime(timezone=True))
    delivery_count = Column(Integer, nullable=False, default=0)
    
    # Full Subscription resource
    resource_data = Column(JSONB, nullable=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index("idx_fhir_subscriptions_tenant", "tenant_id"),
        Index("idx_fhir_subscriptions_status", "status"),
        Index("idx_fhir_subscriptions_resource_type", "resource_type"),
        Index("idx_fhir_subscriptions_active", "tenant_id", "status", postgresql_where=(status == 'active')),
    )
